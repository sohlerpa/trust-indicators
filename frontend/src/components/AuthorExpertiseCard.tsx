import { useEffect, useState } from "react";
import ProgressBar from "./ProgressBar";
import type { AuthorExpertiseTrust } from "../api/types";

export default function AuthorExpertiseCard({
    articleId,
}: {
    articleId: string;
}) {
    const [runId, setRunId] = useState<string | null>(null);
    const [data, setData] = useState<AuthorExpertiseTrust | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setRunId(null);
        setData(null);
        setError(null);

        fetch(`/api/articles/${articleId}/trust/author`, {
            method: "POST",
        })
            .then(r => r.json())
            .then(res => {
                setRunId(res.runId);
            })
            .catch(() => setError("Author analysis failed."));
    }, [articleId]);

    useEffect(() => {
        if (!runId) return;

        let alive = true;

        const poll = async () => {
            try {
                const res = await fetch(
                    `/api/author/result/${runId}`
                );

                if (!res.ok) {
                    setTimeout(poll, 1000);
                    return;
                }

                const data = await res.json();
                if (!alive) return;

                if (data) {
                    setData(data);
                } else {
                    setTimeout(poll, 1000);
                }
            } catch {
                setTimeout(poll, 1500);
            }
        };

        poll();

        return () => {
            alive = false;
        };
    }, [runId]);

    if (error) {
        return (
            <div className="card metaCard">
                <h2>Author Expertise</h2>
                <p className="error">{error}</p>
            </div>
        );
    }

    return (
        <div className="card metaCard">
            <h2>Author Expertise</h2>

            {runId && !data && <ProgressBar runId={runId} />}


            {data && <AuthorResult data={data} />}
        </div>
    );
}


function AuthorResult({ data }: { data: AuthorExpertiseTrust }) {
    const label =
        data.label === "field_expert"
            ? "Field expert"
            : data.label === "not_field_expert"
            ? "Not a field expert"
            : "Uncertain";

    const confidence = Math.max(0, Math.min(1, data.confidence ?? 0));
    const pct = Math.round(confidence * 100);

    return (
        <div className="expertBox">
            <div className="metaRow">
                <div className="metaLeft">
                    <span className={`expertDot ${data.label}`} />
                    <span className="metaLabel">{label}</span>
                </div>

                <span
                    className={`confidencePill ${data.label}`}
                    title={`Confidence: ${pct}%`}
                >
                    {pct}%
                </span>
            </div>

            <div className="expertMeta">
                <div>
                    Author: <strong>{data.author ?? "-"}</strong>
                </div>
                <div>
                    Field: <strong>{data.field ?? "-"}</strong>
                </div>
            </div>

            <div className="confidenceBar">
                <div
                    className={`confidenceFill ${data.label}`}
                    style={{ width: `${pct}%` }}
                />
            </div>

            <p className="metaExplanation">
                {data.explanation ?? "-"}
            </p>
        </div>
    );
}