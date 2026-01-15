import {useEffect, useState} from "react";
import {Link, useParams} from "react-router-dom";
import {getArticle} from "../api/endpoints";
import type {ArticleDetail} from "../api/types";
import CountryFlag from "../components/CountryFlag";

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

                        {(() => {
                            const tone = article.trust_indicators.tone ?? "-";
                            const type = article.trust_indicators.content_type ?? "-";
                            const rationale = article.trust_indicators.tone_type_rationale ?? "-";

                            return (
                                <div className="metaBox">
                                    <div className="metaRow">
                                        <div className="metaLeft">
                                            <span className="metaDot"/>
                                            <span className="metaLabel capitalize">{tone}</span>
                                        </div>

                                        <span className="pill">{type}</span>
                                    </div>

                                    <p className="metaExplanation">{rationale}</p>
                                </div>
                            );
                        })()}
                    </div>
                    <div className="card metaCard">
                        <h2>Fact-Checking</h2>
                        <p>{String(article.trust_indicators.fact_checked)}</p>
                    </div>
                    <div className="card metaCard">
                        <h2>Author Expertise</h2>

                        {(() => {
                            const ae = article.trust_indicators.author_expertise;

                            const label = (ae?.label ?? "uncertain") as
                                | "field_expert"
                                | "not_field_expert"
                                | "uncertain";

                            const labelText =
                                label === "field_expert"
                                    ? "Field expert"
                                    : label === "not_field_expert"
                                        ? "Not a field expert"
                                        : "Uncertain";

                            const confidence = Math.max(0, Math.min(1, ae?.confidence ?? 0));
                            const pct = Math.round(confidence * 100);

                            return (
                                <div className="expertBox">
                                    <div className="metaRow">
                                        <div className="metaLeft">
                                            <span className={`expertDot ${label}`}/>
                                            <span className="metaLabel">{labelText}</span>
                                        </div>

                                        <span
                                            className={`confidencePill ${label}`}
                                            title={`Confidence: ${pct}%`}
                                            aria-label={`Confidence: ${pct}%`}
                                        >
                                            {pct}%
                                        </span>
                                    </div>

                                    <div className="expertMeta">
                                        <div>
                                            Author: <strong>{ae?.author ?? "-"}</strong>
                                        </div>
                                        <div>
                                            Field: <strong>{ae?.field ?? "-"}</strong>
                                        </div>
                                    </div>

                                    <div
                                        className="confidenceBar"
                                        title={`Confidence: ${pct}%`}
                                        aria-label={`Confidence: ${pct}%`}
                                    >
                                        <div
                                            className={`confidenceFill ${label}`}
                                            style={{width: `${pct}%`}}
                                        />
                                    </div>

                                    <p className="metaExplanation">
                                        {ae?.explanation ?? "-"}
                                    </p>
                                </div>
                            );
                        })()}
                    </div>
                    <div className="card metaCard">
                        <h2>Publisher</h2>

                        {(() => {
                            const source = article.source;
                            const type = article.trust_indicators.publisher_type ?? "-";
                            const country = article.trust_indicators.publisher_country;
                            const cc = country ? country.toUpperCase() : "-";

                            return (
                                <div className="metaRow">
                                    <div className="metaLeft">
                                        <span className="metaFlag" title={cc} aria-label={cc}>
                                            <CountryFlag code={country}/>
                                        </span>
                                        <span className="metaLabel">{source}</span>
                                    </div>

                                    <span className="pill">{type}</span>
                                </div>
                            );
                        })()}
                    </div>
                    <div className="card metaCard">
                        <h2>Main Owners</h2>

                        {article.trust_indicators.owners?.length ? (
                            <ul className="ownersNiceList">
                                {article.trust_indicators.owners.map((o) => (
                                    <li key={o.owner} className="metaRow">
                                        <div className="metaLeft">
                                            <span className="metaDot"/>
                                            <span className="metaLabel">{o.owner}</span>
                                        </div>

                                        <span
                                            className="pill"
                                            title={`${o.percent.toFixed(1)}%`}
                                            aria-label={`${o.percent.toFixed(1)}%`}
                                        >
                                            {o.percent.toFixed(1)}%
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
                                {article.trust_indicators.c2pa_info.map((i) => {
                                    const ytId = i.src.includes("youtube.com/embed/")
                                        ? i.src.split("youtube.com/embed/")[1]?.split("?")[0]
                                        : null;

                                    const thumbSrc = ytId
                                        ? `https://img.youtube.com/vi/${ytId}/hqdefault.jpg`
                                        : i.src;

                                    return (
                                        <li key={i.src} className="c2paItem">
                                            <div className="c2paThumbWrap">
                                                <img
                                                    src={thumbSrc}
                                                    alt={i.title ?? (ytId ? "Video" : "Image")}
                                                    className="c2paThumb"
                                                />
                                                {ytId && <div className="playOverlay">▶</div>}
                                            </div>

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
                                    );
                                })}
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