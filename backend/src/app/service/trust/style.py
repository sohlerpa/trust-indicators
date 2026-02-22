from sqlalchemy.orm import Session

from src.modules.tone.tone_classifier import classify_tone
from src.app.models.article import (
    get_article_llm_analysis,
    save_tone_analysis,
)


def analyze_article_style(article, db: Session):
    """
    Analyze and cache tone and content type for an article.

    Returns:
        dict: {
            "tone": str | None,
            "content_type": str | None,
            "tone_type_rationale": str | None
        }
        Cached values are returned if available; otherwise newly computed values.
    """
    row = get_article_llm_analysis(db, article.id)

    if row and row.tone and row.content_type:
        return {
            "tone": row.tone,
            "content_type": row.content_type,
            "tone_type_rationale": row.tone_type_rationale,
        }

    tc = classify_tone(article.content_html)

    if tc.tone == "error" or tc.content_type == "error":
        return {
            "tone": None,
            "content_type": None,
            "tone_type_rationale": tc.rationale,
        }

    save_tone_analysis(db, article.id, tc)

    return {
        "tone": tc.tone,
        "content_type": tc.content_type,
        "tone_type_rationale": tc.rationale,
    }