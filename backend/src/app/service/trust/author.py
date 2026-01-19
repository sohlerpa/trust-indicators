from sqlalchemy.orm import Session

from src.modules.author_expertise.author_expertise_classifier import (
    assess_author_expertise,
)

from src.app.models.models import AuthorExpertise
from src.app.models.article import get_article_llm_analysis, save_author_expertise


def analyze_author(article, db: Session):
    row = get_article_llm_analysis(db, article.id)

    if row and row.author_label:
        return AuthorExpertise(
            label=row.author_label,
            confidence=float(row.author_confidence or 0),
            author=row.author_name,
            field=row.author_field,
            explanation=row.author_explanation,
        )

    ae = assess_author_expertise(
        article.content_html,
        article.author,
        str(article.url),
    )

    if not ae or ae.label == "error":
        return None

    save_author_expertise(db, article.id, ae)
    return ae