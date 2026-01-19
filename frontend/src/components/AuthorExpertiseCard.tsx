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

    if (!data.label) {
        return (
            <div className="card metaCard">
                <h2>Author Expertise</h2>
                <p>-</p>
            </div>
        );
    }
    return (
        <div className="card metaCard">
            <h2>Author Expertise</h2>
            <p>{data.label}</p>
        </div>
    );
}