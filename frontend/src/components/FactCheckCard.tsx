import { useEffect, useState } from "react";
import { getArticleFactCheck, getXPostFactCheck } from "../api/endpoints";
import type { FactCheckTrust } from "../api/types";
import ProgressBar from "./ProgressBar";

export default function FactCheckCard({
    id,
    type,
}: {
    id: string;
    type: "article" | "x";
}) {
    const [data, setData] = useState<FactCheckTrust | null>(null);
    const [runId, setRunId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);


    useEffect(() => {
        setData(null);
        setError(null);
        setRunId(null);

        const fn =
            type === "article"
                ? getArticleFactCheck
                : getXPostFactCheck;

        fn(id)
            .then(res => {
                setRunId(res.runId);
            })
            .catch(() => setError("Fact-checking failed."));
    }, [id, type]);

    useEffect(() => {
        if (!runId) return;

        let alive = true;

        const pollResult = async () => {
            try {
                const res = await fetch(
                    `/api/fact-check/result/${runId}`
                );

                if (!res.ok) {
                    setTimeout(pollResult, 1000);
                    return;
                }

                const result = await res.json();

                if (!alive) return;

                if (result) {
                    setData(result);
                } else {
                    setTimeout(pollResult, 1000);
                }
            } catch {
                setTimeout(pollResult, 1500);
            }
        };

        pollResult();

        return () => {
            alive = false;
        };
    }, [runId]);

    // ─────────────────────────────────────────────

    return (
        <div className="card metaCard">
            <h2>Fact-Checking</h2>

            {runId && !data && <ProgressBar runId={runId} />}

            {error && <p className="error">{error}</p>}

            {data && (
                <>
                    <div className="factCheckSummary">
                        <p>
                            <strong>{data.stats.extractedClaims}</strong>{" "}
                            potentially relevant claims detected
                        </p>
                        <p>
                            <strong>{data.stats.checkedClaims}</strong> checked ·{" "}
                            <strong>{data.stats.droppedClaims}</strong> skipped
                        </p>
                    </div>

                    {data.claims.length === 0 ? (
                        <p className="muted">
                            No claims could be verified against known fact-check sources.
                        </p>
                    ) : (
                        <ul className="factCheckClaims">
                            {data.claims.map((c) => (
                                <li
                                    key={c.id}
                                    className={`claim verdict-${c.verdict}`}
                                >
                                    <p className="claimText">
                                        “{c.claimText}”
                                    </p>

                                    <div className="claimMeta">
                                        <span className="arrow">→</span>{" "}
                                        <strong
                                            className={`verdictText verdictText-${c.verdict}`}
                                        >
                                            {c.verdict}
                                        </strong>{" "}
                                        <span className="confidenceText">
                                            ({Math.round(c.confidence * 100)}%)
                                        </span>
                                    </div>

                                    <p className="summary">{c.summary}</p>
                                </li>
                            ))}
                        </ul>
                    )}
                </>
            )}
        </div>
    );
}