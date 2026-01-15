from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.app.api.schemas import ArticleDetailOut
from src.app.data.sample_data import get_article_by_id
from src.app.service.trust_indicator_enricher import to_article_detail_out
from src.app.service.db_connector import get_db

router = APIRouter()


@router.get("/articles/{article_id}", response_model=ArticleDetailOut)
def get_article(article_id: str, db: Session = Depends(get_db)):
    a = get_article_by_id(article_id)
    if not a:
        raise HTTPException(status_code=404, detail="Article not found")
    return to_article_detail_out(a, db)
