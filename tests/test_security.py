import unittest
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

class SecurityTests(unittest.TestCase):
    def test_health_checker_has_no_hardcoded_webhook(self):
        code = (ROOT / 'scripts/check_deploy.py').read_text(encoding='utf-8')
        self.assertIsNone(re.search(r'https://discord\.com/api/webhooks/\d+/[\w-]+', code), 'Hard-coded webhook must be removed')
