from urllib.parse import urljoin
from bs4 import BeautifulSoup

def extract_img_srcs(content_html: str, article_url: str, api_base_url: str, main_image_url: str | None = None) -> list[str]:
    soup = BeautifulSoup(content_html or "", "html.parser")
    srcs: list[str] = []

    if main_image_url:
        srcs.append(main_image_url)

    for img in soup.find_all(["img", "iframe"]):
        src = (img.get("src") or "").strip()
        if not src:
            continue

        if src.startswith(("http://", "https://")):
            resolved = src
        elif src.startswith("/"):
            resolved = urljoin(api_base_url, src)
        else:
            resolved = urljoin(article_url, src)

        srcs.append(resolved)

    return srcs