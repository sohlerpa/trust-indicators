from fastapi import APIRouter, HTTPException
from app.api.schemas import ArticleDetail
from app.data.sample_data import ARTICLES

router = APIRouter()


@router.get("/articles/{article_id}", response_model=ArticleDetail)
def get_article(article_id: str):
    for a in ARTICLES:
        if a.id == article_id:
            return a
    raise HTTPException(status_code=404, detail="Article not found")
