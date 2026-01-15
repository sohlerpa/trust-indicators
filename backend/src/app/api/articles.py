from fastapi import APIRouter, HTTPException

from src.app.api.schemas import ArticleDetailOut
from src.app.data.sample_data import get_article_by_id
from src.app.service.trust_indicator_enricher import to_article_detail_out

router = APIRouter()


@router.get("/articles/{article_id}", response_model=ArticleDetailOut)
def get_article(article_id: str):
    a = get_article_by_id(article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    return to_article_detail_out(a)
