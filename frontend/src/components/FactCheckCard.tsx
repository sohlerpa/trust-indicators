import { useEffect, useState } from "react";
import { getArticleFactCheck } from "../api/endpoints";
import type { FactCheckTrust } from "../api/types";

export default function FactCheckCard({ articleId }: { articleId: string }) {
    const [data, setData] = useState<FactCheckTrust | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        getArticleFactCheck(articleId)
            .then(setData)
            .catch(() => setError("Fact-checking failed."));
    }, [articleId]);

    if (error) {
        return (
            <div className="card metaCard">
                <h2>Fact-Checking</h2>
                <p className="error">{error}</p>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="card metaCard">
                <h2>Fact-Checking</h2>
                <p className="loading">Verifying claims…</p>
            </div>
        );
    }

    const { stats, claims } = data;

    return (
        <div className="card metaCard">
            <h2>Fact-Checking</h2>

            {/* High-level summary */}
            <div className="factCheckSummary">
                <p>
                    <strong>{stats.extractedClaims}</strong> potentially relevant claims detected
                </p>
                <p>
                    <strong>{stats.checkedClaims}</strong> checked &nbsp;·&nbsp;
                    <strong>{stats.droppedClaims}</strong> skipped (no evidence)
                </p>
            </div>

            {/* Checked claims */}
            {claims.length === 0 ? (
                <p className="muted">
                    No claims could be verified against known fact-check sources.
                </p>
            ) : (
                <ul className="factCheckClaims">
                    {claims.map((c) => (
                        <li key={c.id} className={`claim verdict-${c.verdict}`}>
                            <p className="claimText">“{c.claimText}”</p>

                            <div className="claimMeta">
                                <span className="verdictLine">
                                    <span className="arrow">→</span>{" "}
                                        <strong className={`verdictText verdictText-${c.verdict}`}>{c.verdict}</strong>{" "}
                                    <span className="confidenceText">(confidence: {Math.round(c.confidence * 100)}%)</span>
                              </span>
                            </div>

                            <p className="summary">{c.summary}</p>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}