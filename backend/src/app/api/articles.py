from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from src.app.api.schemas import ArticleBaseOut
from src.app.models.article import get_article_by_id
from src.app.service.article_mapper import to_article_base_out
from src.app.service.db_connector import get_db
from src.app.service.trust.author import analyze_author
from src.app.service.trust.c2pa import analyze_c2pa
from src.app.service.trust.fact_check import run_fact_check
from src.app.service.trust.owners import analyze_owners
from src.app.service.trust.publisher import analyze_publisher
from src.app.service.trust.style import analyze_article_style

router = APIRouter()


@router.get("/articles/{article_id}", response_model=ArticleBaseOut)
def get_article(article_id: str, db: Session = Depends(get_db)):
    a = get_article_by_id(db, article_id)

    if not a:
        raise HTTPException(status_code=404, detail="Article not found")

    return to_article_base_out(a)

@router.get("/articles/{article_id}/trust/style")
def get_article_style(article_id: str, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404)

    return analyze_article_style(article, db)

@router.get("/articles/{article_id}/trust/fact-check")
def get_fact_check(article_id: str, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)
    return run_fact_check(article)

@router.get("/articles/{article_id}/trust/author")
def get_author(article_id: str, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)
    return analyze_author(article, db)

@router.get("/articles/{article_id}/trust/publisher")
def get_publisher(article_id: str, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)
    return analyze_publisher(article, db)

@router.get("/articles/{article_id}/trust/owners")
def get_owners(article_id: str, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)
    return analyze_owners(article, db)

@router.get("/articles/{article_id}/trust/c2pa")
def get_c2pa(article_id: str, db: Session = Depends(get_db)):
    article = get_article_by_id(db, article_id)
    return analyze_c2pa(article)
