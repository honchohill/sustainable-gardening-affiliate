#!/usr/bin/env python3
import os, glob, markdown, re
from pathlib import Path
from html import escape, unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import yaml

WORKDIR = Path(__file__).resolve().parents[1]
CONTENT_DIR = os.path.join(WORKDIR, "content")
SITE_DIR = os.path.join(WORKDIR, "site")
POSTS_DIR = os.path.join(SITE_DIR, "posts")
os.makedirs(POSTS_DIR, exist_ok=True)

AMAZON_TAG = os.getenv("AMAZON_TAG", "homegarde04d7-20")

def build_post(md_path):
    slug = Path(md_path).stem
    md_text = Path(md_path).read_text(encoding="utf-8")
    metadata = {}
    frontmatter = re.match(r"\A---\s*\n(.*?)\n---[ \t]*(?:\n|$)", md_text, re.S)
    if frontmatter:
        try:
            metadata = yaml.safe_load(frontmatter.group(1)) or {}
        except yaml.YAMLError:
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        md_text = md_text[frontmatter.end():]
    if slug == "test-product-review" or metadata.get("editorial_status") != "approved":
        Path(POSTS_DIR, f"{slug}.html").unlink(missing_ok=True)
        return None
    title = str(metadata.get("title") or slug.replace("-", " ").title())
    md_text = re.sub(r'\[AMAZON:([A-Z0-9]{10})\]', lambda m: f"https://amazon.com/dp/{m.group(1)}", md_text)

    def fix_amazon(match):
        original = match.group(0)
        url = urlsplit(unescape(original))
        host = (url.hostname or "").lower()
        if host != "amazon.com" and not host.endswith(".amazon.com"):
            return original
        query = [(k, v) for k, v in parse_qsl(url.query, keep_blank_values=True) if k.lower() != "tag"]
        query.append(("tag", AMAZON_TAG))
        return urlunsplit(url._replace(query=urlencode(query)))

    md_text = re.sub(r"https?://[^\s<>\"'()]+", fix_amazon, md_text)
    html_body = markdown.markdown(md_text, extensions=["extra","tables","toc"])
    canonical = ""
    site_url = os.getenv("SITE_URL", "").strip().rstrip("/")
    try:
        configured = urlsplit(site_url)
        if (configured.scheme in {"http", "https"} and configured.hostname
                and not configured.query and not configured.fragment
                and not configured.username and not configured.password):
            canonical = f'<link rel="canonical" href="{escape(site_url + "/posts/" + slug + ".html", quote=True)}">'
    except ValueError:
        pass
    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        f'<title>{escape(title)}</title>{canonical}</head><body>'
        '<nav aria-label="Main navigation"><a href="../index.html">Verdant — Home</a> | '
        '<a href="../index.html#latest-reviews">All articles</a></nav><main>'
        '<aside aria-label="Affiliate disclosure"><p>As an Amazon Associate I earn from qualifying purchases.</p></aside>'
        '<p class="editorial-note">We have not hands-on tested the products discussed. '
        'Check the cited sources and current product details before making a purchase.</p>'
        f'<article>{html_body}</article></main></body></html>'
    )
    out_path = os.path.join(POSTS_DIR, f"{slug}.html")
    Path(out_path).write_text(html, encoding="utf-8")
    return slug, title

def update_homepage():
    Path(POSTS_DIR, "test-product-review.html").unlink(missing_ok=True)
    posts = []
    drafts = 0
    for md_path in sorted(glob.glob(os.path.join(CONTENT_DIR, "*.md"))):
        post = build_post(md_path)
        if post is None:
            drafts += 1
        else:
            posts.append(post)
    print(f"Published: {len(posts)}; Draft: {drafts}")
    index_path = os.path.join(SITE_DIR, "index.html")
    if os.path.exists(index_path):
        template = Path(index_path).read_text(encoding="utf-8")
    else:
        template = "<html><body><h1>Verdant</h1></body></html>"
    # Own only the marked block and the exact historical builder format.
    template = re.sub(r'<!-- BEGIN GENERATED REVIEWS -->.*?<!-- END GENERATED REVIEWS -->', '', template, flags=re.S)
    template = re.sub(r'<section><h2>Latest Reviews</h2><ul>.*?</ul></section>', '', template, flags=re.S)
    catalog_html = '<!-- BEGIN GENERATED REVIEWS --><section id="latest-reviews" class="wrap"><h2>Latest Reviews</h2><ul>'
    for slug, title in posts:
        catalog_html += f'<li><a href="posts/{slug}.html">{escape(title)}</a></li>'
    catalog_html += "</ul></section><!-- END GENERATED REVIEWS -->"
    if "</body>" in template:
        template = template.replace("</body>", catalog_html + "</body>")
    Path(index_path).write_text(template, encoding="utf-8")

if __name__ == "__main__":
    update_homepage()
    print("Site rebuilt with homepage populated from Markdown.")
