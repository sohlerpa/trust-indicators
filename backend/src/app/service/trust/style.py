from src.modules.tone.tone_classifier import classify_tone

def analyze_article_style(article):
    tc = classify_tone(article.content_html)

    return {
        "tone": tc.tone,
        "content_type": tc.content_type,
        "tone_type_rationale": tc.rationale,
    }