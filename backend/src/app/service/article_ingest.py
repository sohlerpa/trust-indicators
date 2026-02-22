import html as _html
import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from google import genai
from google.genai import types
from pydantic import BaseModel

NORMALIZE_ARTICLE_PROMPT = """
    You are a careful article extraction and normalization system.

    You receive raw HTML of a single web page that contains an article PLUS possible surrounding clutter
    (header/nav/footer, cookie banners, “related articles”, comments, newsletter boxes, paywall prompts, etc.).

    Your job:
    1) Extract ONLY the main article content from the HTML.
    2) Return a STRICT JSON object with:
       - title: string | null
       - author: string | null
       - preview: string  (1–2 sentences, plain text, no quotes, no markdown)
       - content_html: string  (HTML fragment of ONLY the article WITHOUT title)

    Hard rules for content_html:
    - Allowed tags ONLY: h1, h2, p, img, iframe, strong
    - No other tags. No div/span/a/ul/li/br/etc.
    - EXCLUDE the title of the article in the content_hml, it is already returned as the title.
    - Images: ONLY real article images (photos/figures). Do NOT include icons, logos, arrows, emojis, UI graphics, social buttons.
    - If you include <img>, it MUST have a valid absolute "src" URL (https://...) and MAY include "alt".
      Do NOT include base64 images, data: URLs, sprite sheets, favicon, tracking pixels.
    - If you include <iframe>, it MUST have an absolute "src" URL (https://...) and MUST be an actual embedded media element
      that belongs to the article (e.g., an embedded video). No ads.
    - If the article contains real editorial images, include up to 1–3 of them in content_html, keeping their position relative to nearby paragraphs when possible.
    - If you are unsure whether an image is an icon/logo/UI element, exclude it.
    - Remove all navigation, “related content”, captions that are not part of the article, author bio boxes,
      subscription prompts, cookie notices, footers, and anything not belonging to the article body.
    - Keep the original order of the article. Preserve headings and paragraphs.
    - Do NOT invent facts or add anything that is not present in the input HTML.
    - The content_html MUST be a coherent article-only fragment (no surrounding page chrome).

    Output format requirements:
    - Output MUST be valid JSON.
    - Output MUST match exactly this schema and keys:
      { "title": ..., "author": ..., "preview": ..., "content_html": ... }
    - No extra keys. No surrounding text. No markdown code fences.

    Selection guidance:
    - Title: Prefer the article headline (often <h1> or og:title). Exclude site name.
    - Author: Prefer the human author name. Exclude organizations and “By Staff” if a real name exists.
      If no author is reliably present, use null.
    - Preview: 1–2 sentences summarizing the main point(s) of the article.
      It must be grounded in the article text and not contain speculation.

    Input HTML starts after this line.
    HTML:
    """


class NormalizedArticle(BaseModel):
    title: str | None
    author: str | None
    preview: str
    content_html: str


def preprocess_article_from_url(url: str) -> dict[str, Any]:
    """
    Fetch an article URL and produce normalized article fields.

    Returns:
        dict[str, Any]: Title, author, published_at, image_url, preview, and content_html.
    """
    print("Extracting article for ", url)
    html = fetch_html(url)

    soup = BeautifulSoup(html, "html.parser")

    og_img = soup.find("meta", property="og:image")
    image_url = og_img["content"].strip() if og_img and og_img.get("content") else None

    article_tag = soup.find("article")
    content_node = article_tag if article_tag else soup.body

    if content_node:
        for bad in content_node.find_all(["script", "style", "noscript"]):
            bad.decompose()

    published_at = datetime.now(timezone.utc)
    meta_time = soup.find("meta", property="article:published_time") or soup.find("meta", attrs={"name": "pubdate"})
    if meta_time and meta_time.get("content"):
        try:
            published_at = datetime.fromisoformat(meta_time["content"].replace("Z", "+00:00"))
        except Exception:
            pass

    html_for_llm = materialize_images(html, base_url=url)
    html_for_llm = materialize_jwplayer_iframes(html_for_llm)
    normalized = normalize_html(html_for_llm)

    return {
        "title": normalized.get("title"),
        "author": normalized.get("author"),
        "published_at": published_at,
        "image_url": image_url,
        "preview": normalized.get("preview"),
        "content_html": normalized.get("content_html"),
    }


def fetch_html(url: str) -> str:
    """
    Fetch raw HTML content for a URL.

    Returns:
        str: HTML document content.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TrustIndicatorsBot/1.0; +https://example.local)",
        "Accept": "text/html,application/xhtml+xml",
    }
    with httpx.Client(follow_redirects=True, timeout=20.0, headers=headers) as client:
        r = client.get(url)
        r.raise_for_status()

        ct = (r.headers.get("content-type") or "").lower()
        if "text/html" not in ct and "application/xhtml+xml" not in ct:
            if "<html" not in r.text.lower():
                raise ValueError(f"URL did not return HTML (content-type={ct})")

        return r.text


def normalize_html(content: Tag | str) -> dict[str, Any]:
    """
    Normalize article HTML via an LLM into title/author/preview/content_html.

    Returns:
        dict[str, Any]: Normalized article fields.
    """
    html = str(content) if not isinstance(content, str) else content

    print("Normalizing html content with LLM for: ", html[:20])

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY in environment variables.")
    client = genai.Client(api_key=api_key)

    prompt = NORMALIZE_ARTICLE_PROMPT + "\n" + html

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=NormalizedArticle
            )
        )
        data = json.loads(response.text)
        normalized_article = NormalizedArticle(**data)
    except (json.JSONDecodeError, TypeError, Exception) as e:
        raise ValueError(str(e))

    return {
        "title": normalized_article.title,
        "author": normalized_article.author,
        "preview": normalized_article.preview,
        "content_html": normalized_article.content_html,
    }


def _pick_from_srcset(srcset: str) -> str | None:
    """
    Select the highest-resolution URL from a srcset string.

    Returns:
        str | None: Best candidate URL, or None if no candidates exist.
    """
    if not srcset:
        return None

    candidates: list[tuple[float, str]] = []
    for part in srcset.split(","):
        part = part.strip()
        if not part:
            continue
        tokens = part.split()
        url = tokens[0].strip()
        score = 0.0

        if len(tokens) > 1:
            desc = tokens[1].strip()
            try:
                if desc.endswith("w"):
                    score = float(desc[:-1])
                elif desc.endswith("x"):
                    score = float(desc[:-1]) * 10000.0
            except Exception:
                score = 0.0

        candidates.append((score, url))

    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[-1][1]


def materialize_images(raw_html: str, *, base_url: str) -> str:
    """
    Convert image URLs in HTML to absolute URLs and resolve lazy-loading sources.

    Returns:
        str: Updated HTML with materialized <img> tags and absolute URLs.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    for img in soup.find_all("img"):
        src = (img.get("src") or "").strip()

        data_src = (img.get("data-src") or img.get("data-original") or "").strip()
        data_srcset = (img.get("data-srcset") or "").strip()
        srcset = (img.get("srcset") or "").strip()

        chosen = None

        is_placeholder = (not src) or src.startswith("data:") or "transparent" in src.lower()
        if data_src:
            chosen = data_src
        elif data_srcset:
            chosen = _pick_from_srcset(data_srcset)
        elif is_placeholder and srcset:
            chosen = _pick_from_srcset(srcset)

        if chosen:
            abs_url = urljoin(base_url, chosen.strip())
            img["src"] = abs_url
            if "srcset" in img.attrs:
                del img.attrs["srcset"]
            if "data-src" in img.attrs:
                del img.attrs["data-src"]
            if "data-srcset" in img.attrs:
                del img.attrs["data-srcset"]

        src_now = (img.get("src") or "").strip()
        if src_now and not src_now.startswith(("http://", "https://", "data:")):
            img["src"] = urljoin(base_url, src_now)

    for picture in soup.find_all("picture"):
        best = None
        for source in picture.find_all("source"):
            sset = (source.get("srcset") or "").strip()
            if sset:
                cand = _pick_from_srcset(sset)
                if cand:
                    best = cand
        if not best:
            inner_img = picture.find("img")
            if inner_img:
                best = (inner_img.get("data-src") or inner_img.get("src") or "").strip()
                if not best:
                    best = _pick_from_srcset((inner_img.get("srcset") or "").strip() or "")

        if best:
            abs_url = urljoin(base_url, best)
            new_img = soup.new_tag("img")
            new_img["src"] = abs_url
            inner_img = picture.find("img")
            if inner_img and inner_img.get("alt"):
                new_img["alt"] = inner_img.get("alt")
            picture.replace_with(new_img)
        else:
            picture.decompose()

    return str(soup)


def materialize_jwplayer_iframes(raw_html: str) -> str:
    """
    Replace JW Player placeholders with embeddable iframe tags.

    Returns:
        str: Updated HTML with JW Player iframes inserted.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    for el in soup.find_all(attrs={"data-settings": True}):
        ds = el.get("data-settings")
        if not ds:
            continue

        try:
            ds_json = json.loads(_html.unescape(ds))
        except Exception:
            continue

        media_id = ds_json.get("jwplayerMediaId")
        if not media_id:
            continue

        iframe = soup.new_tag("iframe")
        iframe["src"] = f"https://cdn.jwplayer.com/players/{media_id}.html"
        iframe["allow"] = "autoplay; encrypted-media; picture-in-picture"
        iframe["allowfullscreen"] = "true"

        container = el.find_parent(["figure", "section", "div"]) or el
        container.replace_with(iframe)

    return str(soup)