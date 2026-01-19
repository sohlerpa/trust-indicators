from src.modules.provenance_media.extractor import c2pa_for_image_url
from src.app.service.article_mapper import extract_img_srcs
from src.app.models.models import ImageProvenance


def analyze_c2pa(article):
    urls = extract_img_srcs(
        article.content_html,
        article_url=str(article.url),
        api_base_url="http://localhost:8000",
        main_image_url=str(article.image_url) if article.image_url else None,
    )

    images: list[ImageProvenance] = []

    for url in urls:
        info = c2pa_for_image_url(url)
        if not info:
            continue

        images.append(
            ImageProvenance(
                src=url,
                c2pa_present=info.manifest_found,
                issuer=info.issuer,
                title=info.title,
                is_ai_generated=info.is_ai_generated,
            )
        )

    return {
        "c2pa_present": any(i.c2pa_present for i in images),
        "c2pa_info": images,
    }