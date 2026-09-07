#!/usr/bin/env python3
import os, glob, markdown, re
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

WORKDIR = "C:/Users/chris/social-affiliate"
CONTENT_DIR = os.path.join(WORKDIR, "content")
SITE_DIR = os.path.join(WORKDIR, "site")
POSTS_DIR = os.path.join(SITE_DIR, "posts")
os.makedirs(POSTS_DIR, exist_ok=True)

AMAZON_TAG = os.getenv("AMAZON_TAG", "YOUR_AMAZON_TAG")

def build_post(md_path):
    slug = Path(md_path).stem
    md_text = Path(md_path).read_text(encoding="utf-8")
    # Replace [AMAZON:ASIN] placeholder
    md_text = re.sub(r'\[AMAZON:([A-Z0-9]{10})\]', lambda m: f"https://amazon.com/dp/{m.group(1)}?tag={AMAZON_TAG}", md_text)
    # Also fix existing amazon.com/dp/ASIN links
    def fix_amazon(m):
        url = m.group(1)
        return f"{url}?tag={AMAZON_TAG}"
    md_text = re.sub(r'(https?://(?:www\.)?amazon\.com/dp/[A-Z0-9]{10})', fix_amazon, md_text)
    html_body = markdown.markdown(md_text, extensions=["extra","tables","toc"])
    html = f"<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>{slug}</title></head><body>{html_body}</body></html>"
    out_path = os.path.join(POSTS_DIR, f"{slug}.html")
    Path(out_path).write_text(html, encoding="utf-8")
    return slug, md_text

def update_homepage():
    posts = []
    for md_path in glob.glob(os.path.join(CONTENT_DIR, "*.md")):
        slug, md_text = build_post(md_path)
        title = slug.replace("-", " ").title()
        posts.append((slug, title))
    index_path = os.path.join(SITE_DIR, "index.html")
    if os.path.exists(index_path):
        template = Path(index_path).read_text(encoding="utf-8")
    else:
        template = "<html><body><h1>Verdant</h1></body></html>"
    catalog_html = "<section><h2>Latest Reviews</h2><ul>"
    for slug, title in posts:
        catalog_html += f'<li><a href="posts/{slug}.html">{title}</a></li>'
    catalog_html += "</ul></section>"
    if "</body>" in template:
        template = template.replace("</body>", catalog_html + "</body>")
    Path(index_path).write_text(template, encoding="utf-8")

if __name__ == "__main__":
    update_homepage()
    print("Site rebuilt with homepage populated from Markdown.")
