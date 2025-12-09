import json
from dataclasses import dataclass
from typing import Optional, List

from c2pa import Reader, C2paError


@dataclass
class C2PAManifestInfo:
    manifest_found: bool
    title: Optional[str] = None
    issuer: Optional[str] = None
    software: List[str] = None
    thumbnail_uri: Optional[str] = None
    actions: List[str] = None
    is_ai_generated: bool = None


def extract_manifest_info(store: dict) -> C2PAManifestInfo:
    manifests = store.get("manifests", {})
    #print(f"Found {len(manifests)} manifests")
    active_id = store.get("active_manifest")
    #print(f"active manifest is {active_id}")
    active_manifest = manifests.get(active_id, {})

    # Basic fields (from active manifest just like before)
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
    for manifest_id, mf in manifests.items():
        for assertion in mf.get("assertions", []):
            if assertion.get("label") == "c2pa.actions.v2":
                for a in assertion.get("data", {}).get("actions", []):
                    all_actions.append(a.get("action"))

    is_ai_generated = detect_ai_generation(store)

    return C2PAManifestInfo(
        manifest_found=True,
        title=title,
        issuer=issuer,
        software=software,
        thumbnail_uri=thumbnail_uri,
        actions=all_actions,
        is_ai_generated=is_ai_generated[0]
    )

def detect_ai_generation(store: dict) -> tuple[bool, list[str]]:
    """Return (is_ai_generated, evidence_strings)."""
    evidence = []
    is_ai = False

    manifests = store.get("manifests", {})
    for manifest_id, mf in manifests.items():
        for assertion in mf.get("assertions", []):
            if assertion.get("label") != "c2pa.actions.v2":
                continue
            for act in assertion.get("data", {}).get("actions", []):
                if act.get("action") == "c2pa.created":
                    dst = (act.get("digitalSourceType") or "").lower()
                    if dst.endswith("/trainedalgorithmicmedia"):
                        is_ai = True
                        evidence.append(
                            f"{manifest_id}: c2pa.created → digitalSourceType=trainedAlgorithmicMedia"
                        )
                    # optional extra signal
                    sa = act.get("softwareAgent", {}).get("name")
                    if sa:
                        evidence.append(f"{manifest_id}: softwareAgent.name={sa}")

    return is_ai, evidence


class ProvenanceMediaModule:
    """
    Provenance of a medium via C2PA.

    - Returns a C2PAManifestInfo object containing the relevant provenance information
    """

    name = "provenance_media"

    def extract_c2pa_info(self, path_to_medium: str) -> C2PAManifestInfo:
        try:
            with Reader(path_to_medium) as reader:
                store = json.loads(reader.json())
            info = extract_manifest_info(store)
            if getattr(info, "manifest_found", None):
                info.manifest_found = True
            return info
        except (C2paError.Io, FileNotFoundError, json.JSONDecodeError):
            return C2PAManifestInfo(manifest_found=False)