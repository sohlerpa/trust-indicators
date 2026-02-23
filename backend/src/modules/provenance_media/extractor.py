import json
import os
import tempfile
import requests
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from c2pa import Reader, C2paError


@dataclass
class C2PAManifestInfo:
    """
    Structured summary of C2PA manifest metadata.

    Returns:
        C2PAManifestInfo: Data container with parsed C2PA fields.
    """

    manifest_found: bool = False
    title: Optional[str] = None
    issuer: Optional[str] = None
    thumbnail_uri: Optional[str] = None
    software: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    is_ai_generated: bool = False


def detect_ai_generation(store: dict) -> Tuple[bool, List[str]]:
    """
    Detect whether a C2PA store indicates generative AI usage.

    Returns:
        tuple[bool, list[str]]:
            (is_ai_generated, evidence_strings)
    """
    evidence: List[str] = []
    is_ai = False

    manifests = store.get("manifests", {})

    for manifest_id, mf in manifests.items():
        for assertion in mf.get("assertions", []):
            if assertion.get("label") != "c2pa.actions.v2":
                continue

            actions_data = assertion.get("data", {}).get("actions", [])
            for act in actions_data:
                action_name = (act.get("action") or "").lower()

                dst = (act.get("digitalSourceType") or "").lower()
                if "trainedalgorithmicmedia" in dst:
                    is_ai = True
                    evidence.append(
                        f"Manifest[{manifest_id}]: action='{action_name}', digitalSourceType='{dst}'"
                    )

                sa = act.get("softwareAgent")
                if isinstance(sa, str) and sa:
                    evidence.append(f"Manifest[{manifest_id}]: softwareAgent='{sa}'")
                elif isinstance(sa, dict):
                    name = sa.get("name")
                    if name:
                        evidence.append(f"Manifest[{manifest_id}]: softwareAgent='{name}'")

    return is_ai, evidence


def extract_manifest_info(store: dict) -> C2PAManifestInfo:
    """
    Extract relevant metadata from a parsed C2PA store.

    Returns:
        C2PAManifestInfo:
            Parsed manifest summary.
    """
    manifests = store.get("manifests", {})
    active_id = store.get("active_manifest")
    active_manifest = manifests.get(active_id, {})

    title = active_manifest.get("title")
    sig = active_manifest.get("signature_info", {})
    issuer = sig.get("issuer")

    generators = active_manifest.get("claim_generator_info", [])
    software = [g.get("name") for g in generators if "name" in g]

    thumbnail_uri = None
    ingredients = active_manifest.get("ingredients", [])
    if ingredients:
        thumb = ingredients[0].get("thumbnail")
        if thumb:
            thumbnail_uri = thumb.get("identifier")

    all_actions: List[str] = []
    for _, mf in manifests.items():
        for assertion in mf.get("assertions", []):
            if assertion.get("label") == "c2pa.actions.v2":
                actions_list = assertion.get("data", {}).get("actions", [])
                for a in actions_list:
                    action_name = a.get("action")
                    if action_name:
                        all_actions.append(action_name)

    is_ai, _ = detect_ai_generation(store)

    return C2PAManifestInfo(
        manifest_found=True,
        title=title,
        issuer=issuer,
        software=software,
        thumbnail_uri=thumbnail_uri,
        actions=all_actions,
        is_ai_generated=is_ai,
    )


class ProvenanceMediaModule:
    """
    Wrapper for extracting C2PA provenance metadata from local media files.
    """

    name = "provenance_media"

    @staticmethod
    def extract_c2pa_info(path_to_medium: str) -> C2PAManifestInfo:
        """
        Extract C2PA metadata from a local file path.

        Returns:
            C2PAManifestInfo:
                Parsed manifest if present.
                manifest_found=False if parsing fails or no manifest exists.
        """
        if Reader is None:
            return C2PAManifestInfo(manifest_found=False)

        try:
            with Reader(path_to_medium) as reader:
                store = json.loads(reader.json())

            return extract_manifest_info(store)

        except (C2paError.Io, FileNotFoundError):
            return C2PAManifestInfo(manifest_found=False)
        except Exception:
            return C2PAManifestInfo(manifest_found=False)


def c2pa_for_image_url(url: str) -> C2PAManifestInfo | None:
    """
    Download an image temporarily and extract C2PA metadata.

    Returns:
        C2PAManifestInfo:
            If download and extraction succeed.
        None:
            If download fails.
    """
    suffix = os.path.splitext(url.split("?")[0])[1] or ".img"

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            try:
                with requests.get(url, stream=True, timeout=10) as r:
                    r.raise_for_status()

                    for chunk in r.iter_content(chunk_size=1024 * 64):
                        if chunk:
                            tmp.write(chunk)

                return ProvenanceMediaModule.extract_c2pa_info(tmp_path)

            finally:
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    except requests.RequestException:
        return None