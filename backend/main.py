import sys
import json
import argparse
from typing import Any, Dict, List, Tuple, Optional

from factcheck import FactCheckManager

# Diese Module hast du in der URL-Pipeline angelegt:
from factcheck.article_extractor import fetch_url_text
from factcheck.claim_extractor import extract_claims


def _is_checked_result(r):
    if r.get("type") == "multi":
        checks = r.get("checks", [])
        return any("error" not in c for c in checks)
    return False



def analyze_claims(claims: List[str], manager: FactCheckManager) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Prüft eine Liste von Claims und liefert:
    - summary: Aggregationen (overall_score, coverage, counts)
    - results: Liste pro Claim (inkl. claim_text + result)
    """
    results: List[Dict[str, Any]] = []

    for claim in claims:
        res = manager.factcheck(claim)
        res["claim_text"] = claim
        results.append(res)

    # Checked vs Unknown/Error
    checked = [r for r in results if _is_checked_result(r)]
    total = len(results)
    checked_n = len(checked)
    coverage = (checked_n / total) if total else 0.0

    # overall_score nur über checked
    if checked_n:
        overall_score = sum(float(r["score"]) for r in checked) / checked_n
    else:
        overall_score = 0.0

    # Stats
    type_counts: Dict[str, int] = {}
    unknown_n = 0
    error_n = 0

    for r in results:
        t = r.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
        if t == "unknown":
            unknown_n += 1
        if "error" in r:
            error_n += 1

    summary = {
        "overall_score": overall_score,
        "coverage": coverage,
        "total_claims": total,
        "checked_claims": checked_n,
        "unknown_claims": unknown_n,
        "error_claims": error_n,
        "type_counts": dict(sorted(type_counts.items(), key=lambda x: (-x[1], x[0]))),
    }

    return summary, results


def build_report_from_url(url: str, manager: FactCheckManager, max_claims: int) -> Dict[str, Any]:
    text = fetch_url_text(url)
    if not text:
        return {
            "mode": "url",
            "url": url,
            "error": "Konnte Text aus URL nicht extrahieren (oder Seite blockt / zu wenig Inhalt)."
        }

    claims = extract_claims(text, max_claims=max_claims)
    summary, results = analyze_claims(claims, manager)

    return {
        "mode": "url",
        "url": url,
        "extracted_claims": len(claims),
        "summary": summary,
        "results": results,
    }


def build_report_from_text(text: str, manager: FactCheckManager, max_claims: int) -> Dict[str, Any]:
    claims = extract_claims(text, max_claims=max_claims)
    summary, results = analyze_claims(claims, manager)

    return {
        "mode": "text",
        "extracted_claims": len(claims),
        "summary": summary,
        "results": results,
    }


def build_report_from_single_claim(claim: str, manager: FactCheckManager) -> Dict[str, Any]:
    res = manager.factcheck(claim)
    res["claim_text"] = claim

    summary, results = analyze_claims([claim], manager)
    return {
        "mode": "single_claim",
        "summary": summary,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Trust Indicators Fact Checker (MVP): URL/Text -> Claims -> Check -> Report"
    )
    parser.add_argument("--url", type=str, help="URL eines Artikels zum Checken")
    parser.add_argument("--text", type=str, help="Direkter Text (statt URL)")
    parser.add_argument("--max-claims", type=int, default=25, help="Maximale Anzahl extrahierter Claims (Default: 25)")
    parser.add_argument("--out", type=str, default=None, help="Optional: Report als JSON-Datei speichern (z.B. report.json)")

    # Optional: Fallback über positional args (ein Claim als Satz)
    parser.add_argument("claim", nargs="*", help="Fallback: Ein einzelner Claim als Text (ohne --url/--text)")

    args = parser.parse_args()
    manager = FactCheckManager()

    # Modus bestimmen
    if args.url:
        report = build_report_from_url(args.url, manager, args.max_claims)
    elif args.text:
        report = build_report_from_text(args.text, manager, args.max_claims)
    elif args.claim:
        claim_text = " ".join(args.claim).strip()
        report = build_report_from_single_claim(claim_text, manager)
    else:
        print("Bitte nutze entweder:\n"
              '  python main.py --url "https://..."\n'
              '  python main.py --text "Dein Text..."\n'
              '  python main.py "Deutschland hat 84 Millionen Einwohner"\n')
        sys.exit(1)

    # Ausgeben
    output = json.dumps(report, ensure_ascii=False, indent=2)
    print(output)

    # Optional speichern
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(output + "\n")
            print(f"\n✅ Report gespeichert in: {args.out}")
        except OSError as e:
            print(f"\n⚠️ Konnte Report nicht speichern ({args.out}): {e}")


if __name__ == "__main__":
    main()
