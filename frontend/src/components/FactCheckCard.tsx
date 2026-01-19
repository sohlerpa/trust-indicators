import { useEffect, useState } from "react";
import {getArticleFactCheck, getXPostFactCheck} from "../api/endpoints";
import type { FactCheckTrust } from "../api/types";

export default function FactCheckCard({
    id,
    type,
}: {
    id: string;
    type: "article" | "x";
}) {
    const [data, setData] = useState<FactCheckTrust | null>(null);

    useEffect(() => {
        if (!id) return;

        if (type === "article") {
            getArticleFactCheck(id).then(setData);
        } else {
            getXPostFactCheck(id).then(setData);
        }
    }, [id, type]);

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