from src.modules.source_funding.queries import GET_DOMAIN_PUBLISHER_TYPE


def analyze_publisher(article, db):
    """
    Retrieve publisher metadata for the article's source domain.

    Returns:
        dict: {
            "publisher_type": str indicating publisher classification
                              (or "unknown" if not found),
            "publisher_country": str | None indicating country.
        }
    """
    result = db.execute(
        GET_DOMAIN_PUBLISHER_TYPE,
        {"domain": article.source},
    ).fetchone()

    if not result:
        return {
            "publisher_type": "unknown",
            "publisher_country": None,
        }

    return {
        "publisher_type": result.publisher_type,
        "publisher_country": result.country,
    }