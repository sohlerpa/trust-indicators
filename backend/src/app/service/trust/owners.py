from src.modules.source_funding.queries import GET_DOMAIN_OWNERS
from src.app.models.models import OwnerInfo


def analyze_owners(article, db):
    """
    Retrieve ownership information for the article's source domain.

    Returns:
        dict: {
            "owners": list[OwnerInfo] containing owner names
            and their ownership percentages.
        }
    """
    rows = db.execute(
        GET_DOMAIN_OWNERS,
        {"domain": article.source},
    ).fetchall()

    return {
        "owners": [
            OwnerInfo(
                owner=row.name,
                percent=float(row.ownership_percent),
            )
            for row in rows
        ]
    }