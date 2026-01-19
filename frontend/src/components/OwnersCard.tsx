import {useEffect, useState} from "react";
import {getArticleOwners} from "../api/endpoints";
import type {OwnershipTrust} from "../api/types";

export default function OwnersCard({articleId}: {articleId: string}) {
    const [data, setData] = useState<OwnershipTrust | null>(null);

    useEffect(() => {
        getArticleOwners(articleId).then(setData);
    }, [articleId]);

    if (!data) {
        return (
            <div className="card metaCard">
                <h2>Main Owners</h2>
                <p className="loading">Loading ownership…</p>
            </div>
        );
    }

    if (!data.owners?.length) {
        return (
            <div className="card metaCard">
                <h2>Main Owners</h2>
                <p>-</p>
            </div>
        );
    }

    return (
        <div className="card metaCard">
            <h2>Main Owners</h2>
            <ul className="ownersNiceList">
                {data.owners.map(o => (
                    <li key={o.owner} className="metaRow">
                        <span>{o.owner}</span>
                        <span className="pill">{o.percent.toFixed(1)}%</span>
                    </li>
                ))}
            </ul>
        </div>
    );
}