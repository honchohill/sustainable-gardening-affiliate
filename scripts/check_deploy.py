#!/usr/bin/env python3
import os, requests, time
WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1544418828841132114/DdE_QCWQW547uqt8C6N9WPbtixFZX6uYdXqwtaOjmp1lUgH8skva7f2-cHPX-WOiWt3P")
SITE_URL = "https://sustainable-gardening-affiliate.netlify.app/site/posts/test-product-review.html"
def check():
    try:
        r = requests.get(SITE_URL, timeout=10)
        if r.status_code == 200:
            requests.post(WEBHOOK, json={"content": f"✅ Site deploy healthy: {SITE_URL}"})
        else:
            requests.post(WEBHOOK, json={"content": f"⚠️ Site returned {r.status_code}"})
    except Exception as e:
        requests.post(WEBHOOK, json={"content": f"❌ Site check failed: {e}"})
if __name__ == "__main__":
    check()
