#!/usr/bin/env python3
import os, requests, time

WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1544418828841132114/DdE_QCWQW547uqt8C6N9WPbtixFZX6uYdXqwtaOjmp1lUgH8skva7f2-cHPX-WOiWt3P")
SITE_URL = os.getenv("SITE_URL", "https://sustainable-gardening-affiliate.netlify.app")

def check():
    """Check if the Netlify site is serving healthy content."""
    try:
        r = requests.get(SITE_URL, timeout=10)
        if r.status_code == 200 and (r.text.strip() or r.headers.get("content-length", "0") != "0"):
            requests.post(WEBHOOK, json={"content": f"✅ Site deploy healthy: {SITE_URL}\nStatus: 200 OK\nContent: {min(len(r.text), 10)} chars received"})
            return True
        elif r.status_code == 404:
            requests.post(WEBHOOK, json={"content": f"❌ **NETLIFY SITE DOWN** - 404 Not Found\n\nURL: {SITE_URL}\nServer: Netlify is online but no deployment found.\nAction: Check Netlify dashboard for deploy status."})
            return False
        else:
            requests.post(WEBHOOK, json={"content": f"⚠️ **Site Check Warning** - HTTP {r.status_code}\n\nURL: {SITE_URL}\nResponse: {r.status_code} (expected 200)"})
            return False
    except requests.exceptions.Timeout:
        requests.post(WEBHOOK, json={"content": f"🕐 **Site Timeout**\n\n{SITE_URL} didn't respond within 10 seconds."})
        return False
    except requests.exceptions.ConnectionError as e:
        requests.post(WEBHOOK, json={"content": f"🛑 **Site Unreachable**\n\n{SITE_URL} connection failed: {e}"})
        return False
    except Exception as e:
        requests.post(WEBHOOK, json={"content": f"💥 **Check Failed**\n\nError: {type(e).__name__}: {e}"})
        return False

if __name__ == "__main__":
    healthy = check()
    print(f"Site check: {'HEALTHY' if healthy else 'UNHEALTHY'}")
