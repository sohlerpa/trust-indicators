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

    # INFORMATION QUALITY
    "analytical",
    "speculative",
    "conspiratorial",

    # EMOTIONAL INTENSITY
    "sensational",
    "alarmist",
    "angry",

    # ATTITUDE / STANCE
    "critical",
    "supportive",
    "skeptical",

    # RHETORICAL STYLE
    "humorous",
    "ironic",

    # INTENT
    "promotional",

    "error",
]


# Result schema
@dataclass
class ToneClassification:
    content_type: ContentType
    tone: ToneType
    confidence: float
    rationale: str

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


class ToneClassifier:
    def __init__(self):
        """
        Initializes the Gemini client.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None

    def classify_tone(self, text: str) -> ToneClassification:
        """
        Sends the text to the Gemini API to determine its content type and tone.

        Args:
            text (str): The input text to classify.

        Returns:
            ToneClassification: An object containing the classification, tone,
                                confidence score, and a rationale string.
                                Returns an 'error' object if the API call fails.
        """

        # check if client is ready
        if not self.client:
            return ToneClassification("error", "error", 0.0, "Missing GEMINI_API_KEY in environment variables.")

        # Prepare Valid Options
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
                    response_schema=ToneClassification
                )
            )

            data = json.loads(response.text)
            return ToneClassification(**data)

        except (json.JSONDecodeError, TypeError, Exception) as e:
            print(f"Error parsing JSON: {e}")
            return ToneClassification("error", "error", 0.0, str(e))


# Entry point wrapper
def classify_tone(text: str) -> ToneClassification:
    """
    Convenience wrapper to instantiate the classifier and run one prediction.
    """
    classifier = ToneClassifier()
    return classifier.classify_tone(text)
