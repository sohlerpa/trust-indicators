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
            <h2 style={{marginTop: 12}}>
                <span className={`badge ${article.trust_indicators.badge}`}/>
                <span>   </span>
                {article.title}
            </h2>

            <div className="meta">
                <span>{article.source}</span> · <span>{new Date(article.published_at).toLocaleString()}</span>
            </div>

            <div className="articleLayout">
                <div>
                    {article.image_url && <img className="hero" src={article.image_url} alt=""/>}

                    <article
                        className="articleBody card"
                        dangerouslySetInnerHTML={{__html: article.content_html}}
                    />
                </div>

                <div className="card">
                    <div className="card metaCard">
                        <h2>Style</h2>
                        <p>Content Tone: {article.trust_indicators.tone ?? "-"}</p>
                        <p>Content Type: {article.trust_indicators.content_type ?? "-"}</p>
                        <p>{article.trust_indicators.tone_type_rationale ?? "-"}</p>
                    </div>
                    <div className="card metaCard">
                        <h2>Fact-Checking</h2>
                        <p>{String(article.trust_indicators.fact_checked)}</p>
                    </div>
                    <div className="card metaCard">
                        <h2>Publisher</h2>
                        <p>{article.source} ({article.trust_indicators.publisher_type})</p>
                    </div>
                    <div className="card metaCard">
                        <h2>Main Owners</h2>
                        {article.trust_indicators.owners?.length ? (
                            <ul className="ownersList">
                                {article.trust_indicators.owners.map((o) => (
                                    <li key={o.owner} className="ownerRow">
                                        <span className="ownerName">{o.owner}  </span>
                                        <span className="ownerPercent">
                        ({o.percent.toFixed(1)}%)
                    </span>
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p>-</p>
                        )}
                    </div>
                    <div className="card metaCard">
                        <h2>C2PA</h2>

                        {article.trust_indicators.c2pa_info?.length ? (
                            <ul className="c2paList">
                                {article.trust_indicators.c2pa_info.map((i) => (
                                    <li key={i.src} className="c2paItem">
                                        <img
                                            src={i.src}
                                            alt={i.title ?? "Image"}
                                            className="c2paThumb"
                                        />

                                        {i.c2pa_present ? (
                                            <div className="c2paMeta">
                                                <div className="c2paStatus ok">✓ C2PA Manifest present</div>
                                                <div><strong>Title:</strong> {i.title ?? "-"}</div>
                                                <div><strong>Issuer:</strong> {i.issuer ?? "-"}</div>
                                                <div>
                                                    <strong>AI generated:</strong>{" "}
                                                    {i.is_ai_generated ? "yes" : "no"}
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="c2paMeta">
                                                <div className="c2paStatus error">✕ No C2PA data</div>
                                            </div>
                                        )}
                                    </li>
                                ))}
                            </ul>
                        ) : (
                            <p>-</p>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}