from src.modules.author_expertise.author_expertise_classifier import assess_author_expertise, AuthorExpertiseResult


def analyze_author(article):
    #return assess_author_expertise( TODO
    #    article.content_html,
    #    article.author,
    #    str(article.url),
    #)
    return AuthorExpertiseResult(
        author="Test Author",
        article_url="http",
        publisher_domain="spiegel.de",
        field="Geopolitics",
        label="field_expert",
        confidence=0.9,
        explanation="Test explanation"
    )