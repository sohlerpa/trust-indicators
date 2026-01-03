import {useEffect, useState} from "react";
import {Link, useParams} from "react-router-dom";
import {getArticle} from "../api/endpoints";
import type {ArticleDetail} from "../api/types";

export default function ArticlePage() {
    const {id} = useParams();
    const [article, setArticle] = useState<ArticleDetail | null>(null);
    const [err, setErr] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        getArticle(id)
            .then(setArticle)
            .catch((e: unknown) => setErr(e instanceof Error ? e.message : "Unknown error"));
    }, [id]);

    if (err) {
        return (
            <div className="page">
                <Link to="/">← Back</Link>
                <div className="error">Error: {err}</div>
            </div>
        );
    }

    if (!article) return <div className="page">Loading…</div>;

    return (
        <div className="page">
            <Link to="/">← Back</Link>
            <h2 style={{marginTop: 12}}>{article.title}</h2>

            <div className="meta">
                <span>{article.source}</span> · <span>{new Date(article.published_at).toLocaleString()}</span>
            </div>

            {article.image_url && <img className="hero" src={article.image_url} alt=""/>}

            <div className="badgeRow">
                <span className={`badge ${article.trust_indicators.badge}`}/>
                <span className="metaSmall">
          tone: {article.trust_indicators.tone ?? "-"} · type: {article.trust_indicators.content_type ?? "-"} · fact-check:{" "}
                    {String(article.trust_indicators.fact_checked)}
        </span>
            </div>

            <article className="articleBody">
                {article.content.split("\n").map((p, idx) => (
                    <p key={idx}>{p}</p>
                ))}
            </article>
        </div>
    );
}