from src.modules.author_expertise.author_expertise_classifier import assess_author_expertise


def analyze_author(article):
    return assess_author_expertise(
        article.content_html,
        article.author,
        str(article.url),
    )