import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

BUILDER = Path(__file__).resolve().parents[1] / 'scripts' / 'build_site.py'


class BuildSiteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'content').mkdir()
        (self.root / 'site').mkdir()
        shutil.copy2(BUILDER, self.root / 'scripts/build_site.py')
        self.home = '<html><body><header>Original design</header></body></html>'
        (self.root / 'site/index.html').write_text(self.home, encoding='utf-8')
        self.env = dict(os.environ)
        self.env.pop('AMAZON_TAG', None)
        self.env.pop('SITE_URL', None)

    def post(self, text='# Sample', slug='sample'):
        (self.root / f'content/{slug}.md').write_text(text, encoding='utf-8')

    def build(self):
        result = subprocess.run([sys.executable, str(self.root / 'scripts/build_site.py')],
                                cwd=self.root / 'scripts', env=self.env,
                                capture_output=True, text=True)
        self.last_stdout = result.stdout
        self.assertEqual(result.returncode, 0, result.stderr)

    def output(self, slug='sample'):
        return (self.root / f'site/posts/{slug}.html').read_text(encoding='utf-8')

    def test_build_is_portable_without_loading_dotenv(self):
        source = BUILDER.read_text(encoding='utf-8')
        self.assertNotIn('C:/Users/', source)
        self.assertNotIn('load_dotenv', source)
        self.post("---\neditorial_status: approved\n---\n# Sample")
        self.build()
        self.assertIn('Sample', self.output())

    def test_frontmatter_is_metadata_not_body(self):
        self.post('---\neditorial_status: approved\ntitle: "A & B: Guide"\nword_count: 99\n---\n# Body heading\n\nSource text.')
        self.build()
        html = self.output()
        self.assertNotIn('word_count', html)
        self.assertIn('<title>A &amp; B: Guide</title>', html)
        self.assertIn('Source text.', html)
        self.assertIn('A &amp; B: Guide', (self.root / 'site/index.html').read_text())

    def test_only_explicit_approval_publishes_and_cleans_known_drafts(self):
        self.post('---\neditorial_status: approved\n---\n# Approved', 'approved')
        for slug, text in [('legacy', '# Legacy'), ('draft', '---\neditorial_status: draft\n---\n# Draft'), ('invalid', '---\n[broken\n---\n# Invalid'), ('list', '---\n- approved\n---\n# List')]:
            self.post(text, slug)
        posts = self.root / 'site/posts'
        posts.mkdir()
        for slug in ['legacy', 'draft', 'invalid', 'list', 'unrelated']:
            (posts / f'{slug}.html').write_text('previous')
        self.build()
        self.assertEqual(sorted(p.name for p in posts.iterdir()), ['approved.html', 'unrelated.html'])
        self.assertIn('Published: 1; Draft: 4', self.last_stdout)
        self.assertNotIn('posts/legacy.html', (self.root / 'site/index.html').read_text())

    def test_test_product_is_excluded_even_if_approved_and_stale_artifact_removed(self):
        self.post('---\neditorial_status: approved\n---\n# Test', 'test-product-review')
        posts = self.root / 'site/posts'
        posts.mkdir()
        (posts / 'test-product-review.html').write_text('stale')
        self.build()
        self.assertFalse((posts / 'test-product-review.html').exists())
        self.assertNotIn('test-product-review', (self.root / 'site/index.html').read_text())
        (self.root / 'content/test-product-review.md').unlink()
        (posts / 'test-product-review.html').write_text('orphan')
        self.build()
        self.assertFalse((posts / 'test-product-review.html').exists())

    def test_homepage_rebuild_replaces_only_generated_and_exact_legacy_sections(self):
        self.post('---\neditorial_status: approved\n---\n# Sample')
        custom = '<section class="custom"><h2>Latest Reviews</h2><ul><li>Keep me</li></ul></section>'
        legacy = '<section><h2>Latest Reviews</h2><ul><li>Old generated</li></ul></section>'
        original = self.home.replace('</body>', custom + legacy + legacy + '</body>')
        index = self.root / 'site/index.html'
        index.write_text(original)
        self.build()
        first = index.read_text()
        self.assertNotIn('Old generated', first)
        self.assertIn(custom, first)
        self.assertIn('<header>Original design</header>', first)
        self.assertEqual(first.count('posts/sample.html'), 1)
        self.build()
        self.assertEqual(index.read_text(), first)
        self.post('---\neditorial_status: approved\n---\n# New', 'new')
        self.build()
        self.assertEqual(index.read_text().count('posts/new.html'), 1)
        self.assertEqual(index.read_text().count('posts/sample.html'), 1)

    def test_amazon_urls_have_one_tag_preserving_other_query_and_fragment(self):
        from html import unescape
        from urllib.parse import parse_qsl, urlsplit
        import re
        body = ('[Placeholder]([AMAZON:B012345678])\n\n'
                '[Existing](https://www.amazon.com/Product/dp/B012345678?ref=abc&tag=old&tag=again#details)\n\n'
                '[Bare](https://amazon.com/dp/B012345678)\n\n'
                '[Other](https://example.com/dp/B012345678?tag=leave)\n\n'
                '[Spoof](https://amazon.com.evil.test/dp/B012345678?tag=leave)')
        self.post('---\neditorial_status: approved\n---\n' + body)
        for tag in ['homegarde04d7-20', 'custom-20']:
            with self.subTest(tag=tag):
                if tag == 'custom-20':
                    self.env['AMAZON_TAG'] = tag
                self.build()
                links = [unescape(x) for x in re.findall(r'href="([^"]+)"', self.output())]
                amazon = [urlsplit(x) for x in links if urlsplit(x).hostname in ['amazon.com', 'www.amazon.com']]
                self.assertEqual(len(amazon), 3)
                for url in amazon:
                    self.assertEqual([v for k, v in parse_qsl(url.query) if k == 'tag'], [tag])
                self.assertIn(('ref', 'abc'), parse_qsl(amazon[1].query))
                self.assertEqual(amazon[1].fragment, 'details')
                self.assertIn('https://example.com/dp/B012345678?tag=leave', links)
                self.assertIn('https://amazon.com.evil.test/dp/B012345678?tag=leave', links)

    def test_post_shell_has_visible_disclosure_editorial_note_and_navigation(self):
        self.post('---\neditorial_status: approved\n---\n# Sample\n\nOriginal text only.')
        self.build()
        html = self.output()
        self.assertIn('As an Amazon Associate I earn from qualifying purchases.', html)
        self.assertIn('We have not hands-on tested the products discussed.', html)
        self.assertLess(html.index('As an Amazon Associate'), html.index('Original text only.'))
        self.assertIn('<nav', html)
        self.assertIn('href="../index.html"', html)
        self.assertIn('name="viewport" content="width=device-width, initial-scale=1.0"', html)
        self.assertNotIn('rel="canonical"', html)

    def test_canonical_uses_only_configured_valid_site_url(self):
        self.post('---\neditorial_status: approved\n---\n# Sample')
        self.env['SITE_URL'] = 'https://sustainable-gardening-affiliate.netlify.app/'
        self.build()
        self.assertIn('<link rel="canonical" href="https://sustainable-gardening-affiliate.netlify.app/posts/sample.html">', self.output())
        for invalid in ['', 'not-a-url', 'javascript:alert(1)', 'https://example.com/?wrong=1']:
            self.env['SITE_URL'] = invalid
            self.build()
            self.assertNotIn('rel="canonical"', self.output())


if __name__ == '__main__':
    unittest.main()
