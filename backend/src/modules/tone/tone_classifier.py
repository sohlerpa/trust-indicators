import json
import os
from dataclasses import dataclass, asdict
from typing import Literal, get_args

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

ContentType = Literal[
    "news",
    "opinion",
    "analysis",
    "satire",
    "gossip",
    "review",
    "sponsored",
    "other",
    "error"
]

ToneType = Literal[
    "neutral",
    "analytical",
    "speculative",
    "conspiratorial",
    "sensational",
    "alarmist",
    "angry",
    "critical",
    "supportive",
    "skeptical",
    "humorous",
    "ironic",
    "promotional",
    "error",
]


@dataclass
class ToneClassification:
    content_type: ContentType
    tone: ToneType
    confidence: float
    rationale: str

    def to_json(self) -> str:
        """
        Serialize classification result to JSON.
        """
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class ToneClassifier:
    """
    Gemini-based classifier for article tone and content type.
    """

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None

    def classify_tone(self, text: str) -> ToneClassification:
        """
        Classify content type and tone using Gemini.

        Returns:
            ToneClassification:
                Valid classification if successful.
                content_type="error", tone="error" if classification fails.
        """

        if not self.client:
            return ToneClassification(
                "error",
                "error",
                0.0,
                "Missing GEMINI_API_KEY in environment variables."
            )

        valid_content_types = [t for t in get_args(ContentType) if t != "error"]
        valid_tones = [t for t in get_args(ToneType) if t != "error"]

        prompt = f"""
        Classify the text by the given content_types and tones.

        1. Look at all content_types and tones.
        2. Decide which is the most plausible match.
        3. Neutral is only allowed if strictly factual.
        4. If multiple tones apply, choose the STRONGEST one.

        Available content_types: {valid_content_types}
        Available tones: {valid_tones}

        TEXT TO CLASSIFY:
        {text}
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ToneClassification,
                ),
            )

            if not response or not response.text:
                return ToneClassification("error", "error", 0.0, "Empty Gemini response.")

            data = json.loads(response.text)
            return ToneClassification(**data)

        except (json.JSONDecodeError, TypeError, Exception) as e:
            return ToneClassification("error", "error", 0.0, str(e))


def classify_tone(text: str) -> ToneClassification:
    """
    Convenience wrapper to classify a single text.
    """
    return ToneClassifier().classify_tone(text)