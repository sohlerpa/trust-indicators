import {useEffect, useState} from "react";
import {getArticleAuthor} from "../api/endpoints";
import type {AuthorExpertiseTrust} from "../api/types";

export default function AuthorExpertiseCard({articleId}: {articleId: string}) {
    const [data, setData] = useState<AuthorExpertiseTrust | null>(null);

    useEffect(() => {
        getArticleAuthor(articleId).then(setData);
    }, [articleId]);

    if (!data) {
        return (
            <div className="card metaCard">
                <h2>Author Expertise</h2>
                <p className="loading">Evaluating author credibility…</p>
            </div>
        );
    }

    const label =
        data.label === "field_expert"
            ? "Field expert"
            : data.label === "not_field_expert"
                ? "Not a field expert"
                : "Uncertain";

    const confidence = Math.max(0, Math.min(1, data.confidence ?? 0));
    const pct = Math.round(confidence * 100);

    return (
        <div className="card metaCard">
            <h2>Author Expertise</h2>

            <div className="expertBox">
                <div className="metaRow">
                    <div className="metaLeft">
                        <span className={`expertDot ${data.label}`}/>
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
                        style={{width: `${pct}%`}}
                    />
                </div>

                <p className="metaExplanation">
                    {data.explanation ?? "-"}
                </p>
            </div>
        </div>
    );
}