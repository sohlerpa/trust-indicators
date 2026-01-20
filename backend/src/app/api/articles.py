import uuid

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from src.app.api.schemas import ArticleBaseOut
from src.app.models.article import get_article_by_id
from src.app.service.article_mapper import to_article_base_out
from src.app.service.db_connector import get_db
from src.app.service.progress import set_progress, results
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

@router.post("/articles/{article_id}/trust/fact-check")
def start_article_fact_check(
    article_id: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(404)

    run_id = f"article:{article.id}:{uuid.uuid4().hex[:8]}"

    background.add_task(
        run_and_store_fact_check,
        run_id=run_id,
        article=article,
        db=db,
    )

    return {"runId": run_id}

@router.post("/articles/{article_id}/trust/author")
def start_author_check(
    article_id: str,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(404)

    run_id = f"author:{article.id}:{uuid.uuid4().hex[:8]}"

    background.add_task(
        run_and_store_author_check,
        run_id=run_id,
        article=article,
        db=db,
    )

    return {"runId": run_id}

@router.get("/author/result/{run_id}")
def get_author_result(run_id: str):
    return results.get(run_id)

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


def run_and_store_fact_check(
    *,
    run_id: str,
    article,
    db: Session,
):
    dto = run_fact_check(
        article,
        db,
        progress=lambda s, p: set_progress(run_id, s, p),
    )

    results[run_id] = dto


def run_and_store_author_check(
    *,
    run_id: str,
    article,
    db: Session,
):
    dto = analyze_author(
        article,
        db,
        progress=lambda s, p: set_progress(run_id, s, p),
    )

    results[run_id] = dto