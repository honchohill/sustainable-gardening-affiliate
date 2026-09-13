import contextlib
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def server(status=200, body=b'<html><title>Verdant</title></html>', content_length=None):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(status)
            self.send_header('Content-Type', 'text/html')
            if content_length is not None:
                self.send_header('Content-Length', str(content_length))
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(httpd.server_port)
    finally:
        httpd.shutdown()
        httpd.server_close()
        thread.join()


class PublishTests(unittest.TestCase):
    def test_push_stages_only_allowlisted_files_and_commits_then_pushes(self):
        publisher = load('publish')
        candidates = ['content/review.md', 'site/index.html', 'site/posts/old.html', 'scripts/build_site.py', '.env', '.env.example', 'logs/run.log', 'metrics/report.md', 'site/.env', 'site/logs/x.html', 'content/metrics.md', 'scripts/unknown.py']
        def fake_run(command, **kwargs):
            output = ''
            if command[1:2] == ['ls-files']:
                output = '\0'.join(candidates) + '\0'
            if command[1:4] == ['diff', '--cached', '--quiet']:
                return subprocess.CompletedProcess(command, 1, '', '')
            return subprocess.CompletedProcess(command, 0, output, '')
        with patch.object(publisher.subprocess, 'run', side_effect=fake_run) as run:
            self.assertEqual(publisher.main(['--push']), 0)
        commands = [call.args[0] for call in run.call_args_list]
        stage = next(c for c in commands if c[:2] == ['git', 'add'])
        self.assertEqual(set(stage[3:]), set(candidates[:4]))
        self.assertEqual(stage[:3], ['git', 'add', '--'])
        self.assertEqual(commands[-2][:2], ['git', 'commit'])
        self.assertEqual(commands[-1], ['git', 'push'])

    def test_validation_failure_stops_before_git(self):
        publisher = load('publish')
        for failure_index in (0, 1):
            responses = [subprocess.CompletedProcess([], 0)] * failure_index + [subprocess.CalledProcessError(1, ['SECRET'])]
            with patch.object(publisher.subprocess, 'run', side_effect=responses) as run, contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(publisher.main(['--push']), 1)
                self.assertFalse(any(c.args[0][0] == 'git' for c in run.call_args_list))
                self.assertNotIn('SECRET', output.getvalue())

    def test_existing_index_refused_without_mutation(self):
        publisher = load('publish')
        def fake_run(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, '.env\0' if command[0] == 'git' else '', '')
        with patch.object(publisher.subprocess, 'run', side_effect=fake_run) as run:
            self.assertEqual(publisher.main(['--push']), 1)
        self.assertFalse(any(c.args[0][1] in ('add', 'commit', 'push') for c in run.call_args_list))

    def test_shell_wrapper_delegates_and_forwards_arguments(self):
        text = (ROOT / 'scripts/publish.sh').read_text()
        self.assertIn('publish.py', text)
        self.assertIn('"$@"', text)
        self.assertNotIn('hugo', text)
        self.assertNotIn('rsync', text)
        self.assertNotIn('git add', text)

    def test_default_runs_build_and_tests_without_git(self):
        self.assertTrue((ROOT / 'scripts/publish.py').exists(), 'Python publisher required')
        publisher = load('publish')
        with patch.object(publisher.subprocess, 'run') as run:
            run.return_value = subprocess.CompletedProcess([], 0, '', '')
            self.assertEqual(publisher.main([]), 0)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands, [[sys.executable, 'scripts/build_site.py'], [sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v']])
        for call in run.call_args_list:
            self.assertEqual(call.kwargs['cwd'], ROOT)


class HealthTests(unittest.TestCase):
    def test_truncated_response_reports_failure_without_traceback(self):
        checker = load('check_deploy')
        with server(content_length=999) as url, patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': ''}), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(checker.main(['--url', url]), 1)
            self.assertIn('UNHEALTHY', output.getvalue())

    def test_rejects_wrong_content_status_redirect_and_oversized_body(self):
        checker = load('check_deploy')
        for status, body in [(200, b'<html>Other site</html>'), (404, b'Verdant'), (503, b'Verdant'), (302, b'Verdant'), (200, b'Verdant' + b'x' * 1048576)]:
            with self.subTest(status=status, size=len(body)), server(status, body) as url, patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': ''}), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(checker.main(['--url', url]), 1)
                self.assertIn('UNHEALTHY', output.getvalue())

    def test_notification_failure_is_optional_bounded_and_secret_safe(self):
        checker = load('check_deploy')
        with server() as url, patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': 'https://discord.invalid/SECRET'}), patch.object(checker.requests, 'post', side_effect=checker.requests.ConnectionError('SECRET')) as post, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertTrue(checker.check(url))
            self.assertEqual(post.call_count, 1)
            self.assertEqual(post.call_args.kwargs['timeout'], 10)
            self.assertFalse(post.call_args.kwargs['allow_redirects'])
            self.assertNotIn('SECRET', output.getvalue())

    def test_request_failure_never_prints_secret(self):
        checker = load('check_deploy')
        with patch.object(checker.requests, 'get', side_effect=checker.requests.Timeout('SECRET')), patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': ''}), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertFalse(checker.check('https://invalid/?token=SECRET'))
            self.assertNotIn('SECRET', output.getvalue())

    def test_healthy_without_webhook_cli(self):
        with server() as url, patch.dict(os.environ, {'DISCORD_WEBHOOK_URL': ''}):
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/check_deploy.py'), '--url', url], capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('HEALTHY', result.stdout)
        self.assertNotIn('UNHEALTHY', result.stdout)
