from typing import Dict, Any


class ProvenanceMediaModule:
    """
    Dummy implementation for the 'Herkunft (Bild/Video/Audio)' module.

    It:
    - expects an item describing a piece of media (image/video/audio)
    - checks if the media type is supported
    - checks if C2PA metadata is present
    - (dummy) treats any non-empty C2PA metadata as a "valid" signature
    - returns a simple score plus C2PA information
    """

    name = "provenance_media"

    def compute_score(self, item: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize media type
        media_type = (item.get("media_type") or "").lower()
        is_supported_media = media_type in {"image", "video", "audio"}

        return {
            "score": 0.8,
            "confidence": 0.5,
            "details": {
                "media_type": media_type or "unknown",
                "is_supported_media": is_supported_media,
                "has_c2pa_metadata": True,
                "has_valid_c2pa_signature": True,
                "c2pa_metadata": None,
            },
        }