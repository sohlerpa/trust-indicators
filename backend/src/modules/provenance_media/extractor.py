import json
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from c2pa import Reader, C2paError


# Return schema
@dataclass
class C2PAManifestInfo:
    manifest_found: bool = False
    title: Optional[str] = None
    issuer: Optional[str] = None
    thumbnail_uri: Optional[str] = None
    software: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    is_ai_generated: bool = False


def detect_ai_generation(store: dict) -> Tuple[bool, List[str]]:
    """
    Scans the C2PA store for indicators of Generative AI usage.
    Returns (is_ai_generated, list_of_evidence_strings).
    """
    evidence = []
    is_ai = False

    manifests = store.get("manifests", {})

    for manifest_id, mf in manifests.items():
        assertions = mf.get("assertions", [])

        for assertion in assertions:
            if assertion.get("label") != "c2pa.actions.v2":
                continue

            actions_data = assertion.get("data", {}).get("actions", [])
            for act in actions_data:
                # Check 1: digitalSourceType
                if act.get("action") == "c2pa.created":
                    dst = (act.get("digitalSourceType") or "").lower()
                    if "trainedalgorithmicmedia" in dst:
                        is_ai = True
                        evidence.append(
                            f"Manifest[{manifest_id}]: digitalSourceType='{dst}'"
                        )

                    # Check 2: Software Agent
                    software_agent = act.get("softwareAgent", {}).get("name")
                    if software_agent:
                        evidence.append(f"Manifest[{manifest_id}]: softwareAgent='{software_agent}'")

    return is_ai, evidence


def extract_manifest_info(store: dict) -> C2PAManifestInfo:
    manifests = store.get("manifests", {})
    active_id = store.get("active_manifest")
    active_manifest = manifests.get(active_id, {})

    # Basic fields (from active manifest)
    title = active_manifest.get("title")
    sig = active_manifest.get("signature_info", {})
    issuer = sig.get("issuer")

    # Software
    generators = active_manifest.get("claim_generator_info", [])
    software = [g.get("name") for g in generators if "name" in g]

    # Thumbnail
    thumbnail_uri = None
    ingredients = active_manifest.get("ingredients", [])
    if ingredients:
        thumb = ingredients[0].get("thumbnail")
        if thumb:
            thumbnail_uri = thumb.get("identifier")

    # Collect Actions
    all_actions: List[str] = []
    for _, mf in manifests.items():
        for assertion in mf.get("assertions", []):
            if assertion.get("label") == "c2pa.actions.v2":
                actions_list = assertion.get("data", {}).get("actions", [])
                for a in actions_list:
                    action_name = a.get("action")
                    if action_name:
                        all_actions.append(action_name)

    # Detect AI
    is_ai, ai_evidence = detect_ai_generation(store)

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
    Provenance of a medium via C2PA.
    Wrapper to extract C2PA/CAI manifest data if present.
    """
    name = "provenance_media"

    @staticmethod
    def extract_c2pa_info(path_to_medium: str) -> C2PAManifestInfo:
        if Reader is None:
            return C2PAManifestInfo(
                manifest_found=False,
            )

        try:
            with Reader(path_to_medium) as reader:
                store = json.loads(reader.json())

            return extract_manifest_info(store)

        except (C2paError.Io, FileNotFoundError):
            return C2PAManifestInfo(manifest_found=False)
        except Exception:
            # Generic catch-all for C2PA parsing errors
            return C2PAManifestInfo(manifest_found=False)
