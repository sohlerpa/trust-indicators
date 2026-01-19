import {useEffect, useState} from "react";
import {getArticleFactCheck} from "../api/endpoints";
import type {FactCheckTrust} from "../api/types";

export default function FactCheckCard({articleId}: {articleId: string}) {
    const [data, setData] = useState<FactCheckTrust | null>(null);

    useEffect(() => {
        getArticleFactCheck(articleId).then(setData);
    }, [articleId]);

    if (!data) {
        return (
            <div className="card metaCard">
                <h2>Fact-Checking</h2>
                <p className="loading">Verifying claims…</p>
            </div>
        );
    }

    return (
        <div className="card metaCard">
            <h2>Fact-Checking</h2>
            <p>{String(data.fact_checked)}</p>
        </div>
    );
}