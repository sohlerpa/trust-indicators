import json
from dataclasses import dataclass, asdict
from typing import List, Dict

from backend.src.modules.tone.HFAdapter import HFJsonAdapter

CONTENT_TYPES: List[str] = [
    "news",                # factual reporting of recent events
    "opinion",             # columns, commentary, first-person takes
    "analysis",            # explainer, backgrounder, data/context pieces
    "satire",              # parody/comedic distortion of facts
    "gossip",              # rumors/celebrity/private-life focus
    "review",              # product/book/film evaluations
    "press_release",       # organization-authored announcements
    "sponsored",           # advertorial/paid content
    "blog_personal",       # diary-like or informal personal blog
    "academic_summary",    # summary of research, papers, studies
    "forum_social",        # short social post or forum thread
    "other"
]

TONES: List[str] = [
    "neutral", "objective", "sober", "sensational", "alarmist",
    "humorous", "ironic", "sarcastic", "promotional", "empathetic",
    "critical", "skeptical", "optimistic", "pessimistic",
    "speculative", "conspiratorial", "angry"
]

# =========================
# Result schema
# =========================
@dataclass
class ToneClassification:
    content_type: str
    tone: str
    confidence: float
    content_type_scores: Dict[str, float]
    tone_scores: Dict[str, float]
    rationale: str
    evidence_spans: List[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, separators=(",", ":"))


# =========================
# Core classifier
# =========================
class ToneClassifier:
    def __init__(self, llm: HFJsonAdapter, max_chars: int = 2000):
        """
        llm: an instance of HFJsonAdapter with a local text-generation pipeline
        """
        if llm is None:
            raise ValueError("A local HFJsonAdapter instance is required (no fallback).")
        self.llm = llm
        self.max_chars = max_chars

    def _repair_zero_scores(self, scores: Dict[str, float], chosen: str) -> Dict[str, float]:
        # If everything is 0 or missing, assign a sane default to the chosen label.
        if not scores or max(scores.values() or [0.0]) <= 0.0:
            return {chosen: 0.9}
        return scores

    def classify_tone(self, text: str) -> ToneClassification:
        text = (text or "").strip()
        if not text:
            raise ValueError("Empty input text.")

        snippet = self._smart_truncate(text, self.max_chars)
        prompt = self._build_prompt(snippet)
        raw = self.llm.classify(prompt)

        # Top-level list safeguard (some models return [ { ... } ])
        if isinstance(raw, list) and raw and isinstance(raw[0], dict):
            raw = raw[0]

        ct_scores = self._coerce_scores(raw.get("content_type_scores", {}), CONTENT_TYPES)
        tn_scores = self._coerce_scores(raw.get("tone_scores", {}), TONES)

        # Ensure all labels exist (fill missing with 0.0)
        for k in CONTENT_TYPES:
            ct_scores.setdefault(k, 0.0)
        for k in TONES:
            tn_scores.setdefault(k, 0.0)

        content_type = str(raw.get("content_type", "other"))
        tone = str(raw.get("tone", "neutral"))

        if content_type not in CONTENT_TYPES:
            # Snap to best scored known label, else 'other'
            content_type = max(ct_scores.items(), key=lambda kv: kv[1])[0] if any(ct_scores.values()) else "other"

        if tone not in TONES:
            tone = max(tn_scores.items(), key=lambda kv: kv[1])[0] if any(tn_scores.values()) else "neutral"

        # Repair if the model returned all zeros
        ct_scores = self._repair_zero_scores(ct_scores, content_type)
        tn_scores = self._repair_zero_scores(tn_scores, tone)

        # confidence ~= min(top content-type score, top tone score) clipped to [0,1]
        top_ct = ct_scores.get(content_type, 0.0)
        top_tn = tn_scores.get(tone, 0.0)
        confidence = max(0.0, min(1.0, min(top_ct, top_tn)))

        rationale = str(raw.get("rationale", ""))[:400]
        spans = [str(s)[:140] for s in raw.get("evidence_spans", [])][:3]

        if not spans:
            # If the model ignored spans, provide minimal context to avoid empty arrays.
            spans = [snippet[:140]]

        return ToneClassification(
            content_type=content_type,
            tone=tone,
            confidence=confidence,
            content_type_scores=ct_scores,
            tone_scores=tn_scores,
            rationale=rationale,
            evidence_spans=spans
        )

    def _coerce_scores(self, raw_scores, allowed_labels: List[str]) -> Dict[str, float]:
        """
        Accepts:
          - dict: {"news": 0.7, ...}
          - list of dicts: [{"label":"news","score":0.7}, ...]
          - list of pairs: [["news",0.7], ...] or [("news",0.7), ...]
          - list of floats with len == len(allowed_labels): [0.7, 0.1, ...] (zips in order)
          - anything else -> {}
        Returns a filtered {label: float} with unknown labels dropped and NaNs -> 0.0.
        """
        out: Dict[str, float] = {}

        def _clamp(x):
            try:
                v = float(x)
                if v != v:  # NaN
                    return 0.0
                return max(0.0, min(1.0, v))
            except Exception:
                return 0.0

        if isinstance(raw_scores, dict):
            for k, v in raw_scores.items():
                if k in allowed_labels:
                    out[k] = _clamp(v)
            return out

        if isinstance(raw_scores, list):
            # list of dicts with label/score
            if raw_scores and isinstance(raw_scores[0], dict):
                for d in raw_scores:
                    k = d.get("label") or d.get("name") or d.get("class")
                    if k in allowed_labels:
                        out[k] = _clamp(d.get("score", d.get("prob", d.get("p", 0.0))))
                return out
            # list of pairs
            if raw_scores and isinstance(raw_scores[0], (list, tuple)) and len(raw_scores[0]) >= 2:
                for k, v, *rest in raw_scores:
                    if k in allowed_labels:
                        out[k] = _clamp(v)
                return out
            # list of floats (zip by position)
            if len(raw_scores) == len(allowed_labels) and all(isinstance(x, (int, float)) for x in raw_scores):
                for k, v in zip(allowed_labels, raw_scores):
                    out[k] = _clamp(v)
                return out

        return out

    # ---------- Prompt ----------
    def _build_prompt(self, text: str) -> str:
        return (
                "Classify the text by content_type and tone. Be honest: if it is sensational, alarmist or tabloid-like, say so.\n"
                "Return STRICT JSON ONLY wrapped in <json>...</json>. No explanations outside the tags.\n\n"
                f"content_types={CONTENT_TYPES}\n"
                f"tones={TONES}\n\n"
                "EXAMPLES (format only):\n"
                "<json>{\"content_type\":\"news\",\"tone\":\"sober\",\"confidence\":0.71,"
                "\"content_type_scores\":{\"news\":0.71,\"analysis\":0.20},"
                "\"tone_scores\":{\"sober\":0.75,\"objective\":0.20},"
                "\"rationale\":\"Factual description without emotive framing.\","
                "\"evidence_spans\":[\"according to documents released Tuesday\"]}</json>\n\n"
                "<json>{\"content_type\":\"news\",\"tone\":\"sensational\",\"confidence\":0.84,"
                "\"content_type_scores\":{\"news\":0.84,\"opinion\":0.10},"
                "\"tone_scores\":{\"sensational\":0.90,\"alarmist\":0.40},"
                "\"rationale\":\"Dramatic language typical of tabloids.\","
                "\"evidence_spans\":[\"Ballon-Terror!\",\"hybrider Angriff\"]}</json>\n\n"
                "TEXT:\n<<<\n" + text + "\n>>>\n"
                                        "Output ONLY JSON inside <json>...</json>."
        )

    # ---------- Utilities ----------
    @staticmethod
    def _smart_truncate(s: str, max_len: int) -> str:
        if len(s) <= max_len:
            return s
        head = s[: int(max_len * 0.6)]
        tail = s[-int(max_len * 0.35):]
        return head + "\n[…]\n" + tail


# =========================
# Thin functional wrapper
# =========================
def classify_tone(text: str, llm: HFJsonAdapter) -> ToneClassification:
    """
    Functional entry point (no fallback). Pass an HFJsonAdapter wired to your local pipeline.
    """
    return ToneClassifier(llm=llm).classify_tone(text)

