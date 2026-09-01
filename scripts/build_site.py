#!/usr/bin/env python3
"""
build_site.py
Converts markdown reviews to HTML and commits site changes.
"""
import os
import glob
import markdown
from datetime import datetime
import subprocess

WORKDIR = "C:/Users/chris/social-affiliate"
CONTENT_DIR = os.path.join(WORKDIR, "content")
SITE_POSTS = os.path.join(WORKDIR, "site", "posts")
LOGS_DIR = os.path.join(WORKDIR, "logs")
os.makedirs(SITE_POSTS, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

log_path = os.path.join(LOGS_DIR, f"build-{datetime.now().date().isoformat()}.log")
with open(log_path, "w") as log:
    log.write(f"=== Build {datetime.now().isoformat()} ===\n")
    for md_path in glob.glob(os.path.join(CONTENT_DIR, "*.md")):
        slug = os.path.splitext(os.path.basename(md_path))[0]
        out_path = os.path.join(SITE_POSTS, f"{slug}.html")
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        html_body = markdown.markdown(md_text, extensions=["extra", "tables", "toc"])
        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>{slug}</title>
<link rel="stylesheet" href="../index.css">
</head>
<body>
<article>
{html_body}
</article>
</body>
</html>"""
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        log.write(f"Converted {md_path} -> {out_path}\n")
    log.write("Build complete\n")

# git commit
os.chdir(WORKDIR)
subprocess.run(["git", "add", "site/posts", "logs"], check=False)
subprocess.run(["git", "commit", "-m", f"auto: site build {datetime.now().date().isoformat()}"], check=False)
