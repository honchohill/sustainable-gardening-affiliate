#!/usr/bin/env python3
"""Check the deployed site; Discord is optional, never a health prerequisite."""
import argparse
import os
import re
import requests
from urllib3.exceptions import HTTPError

MAX_BYTES = 1024 * 1024
EXPECTED_MARKER = re.compile(rb'<title[^>]*>\s*Verdant\b', re.I)


def check(url=None):
    url = url or os.getenv('SITE_URL', 'https://sustainable-gardening-affiliate.netlify.app')
    try:
        with requests.get(url, timeout=10, allow_redirects=False, stream=True) as response:
            healthy = False
            reason = f'HTTP {response.status_code}'
            if response.status_code == 200:
                body = response.raw.read(MAX_BYTES + 1, decode_content=True)
                healthy = len(body) <= MAX_BYTES and bool(EXPECTED_MARKER.search(body))
                reason = 'Verdant marker verified' if healthy else 'missing Verdant marker or oversized response'
    except (requests.RequestException, HTTPError, OSError, ValueError):
        healthy, reason = False, 'request failed'
    message = f"Site check: {'HEALTHY' if healthy else 'UNHEALTHY'} ({reason})"
    print(message)
    webhook = os.getenv('DISCORD_WEBHOOK_URL', '').strip()
    if webhook:
        try:
            with requests.post(webhook, json={'content': message}, timeout=10, allow_redirects=False, stream=True) as notification:
                if not 200 <= notification.status_code < 300:
                    print('Discord notification failed (HTTP error).')
        except (requests.RequestException, OSError, ValueError):
            print('Discord notification failed (request error).')
    return healthy


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', help='Site URL (defaults to SITE_URL)')
    args = parser.parse_args(argv)
    return 0 if check(args.url) else 1


if __name__ == '__main__':
    raise SystemExit(main())
