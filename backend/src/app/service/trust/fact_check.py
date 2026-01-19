from sqlalchemy.orm import Session

from src.app.models.article import get_fact_check_cache, upsert_fact_check_cache
from src.modules.fact_checking.fact_checking import FactCheckTrustDTO, check_facts_for_html


def run_fact_check(article, db: Session) -> FactCheckTrustDTO:
    cached = get_fact_check_cache(db, article.id)
    if cached is not None:
        print(f"Using cached fact check for {article.id}")
        return cached

    print(f"Checking claims for {article.id}")
    dto = check_facts_for_html(article.content_html, article_id=article.id)

    upsert_fact_check_cache(db, article.id, dto, model="gemini-2.5-flash")
    return dto

def run_fact_check_for_text(*, text: str, source_id: str, db: Session,):
    fake_html = f"<p>{text}</p>"

    return check_facts_for_html(
        fake_html,
        article_id=source_id,
    )