import {useEffect, useState} from "react";
import {Link} from "react-router-dom";
import {fetchFactCheckResult, getArticle, startArticleFactCheck} from "../api/endpoints";
import type {ArticleBase, FactCheckTrust} from "../api/types";
import {useNavigate, useParams} from "react-router-dom";

import FactCheckCard from "../components/FactCheckCard";
import AuthorExpertiseCard from "../components/AuthorExpertiseCard";
import StyleCard from "../components/StyleCard";
import C2PACard from "../components/C2PACard";
import OwnershipPublisherCard from "../components/PublisherOwnershipCars";
import HighlightedArticleBody from "../components/HighlightedArticleBody";

export default function ArticlePage() {
    const {id} = useParams();
    const navigate = useNavigate();
    const [article, setArticle] = useState<ArticleBase | null>(null);
    const [fact, setFact] = useState<FactCheckTrust | null>(null);
    const [factRunId, setFactRunId] = useState<string | null>(null);
    const [factError, setFactError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        setArticle(null);
        getArticle(id).then(setArticle).catch(() => setArticle(null));
    }, [id]);

    useEffect(() => {
        if (!id) return;

        setFact(null);
        setFactRunId(null);
        setFactError(null);

        startArticleFactCheck(id)
            .then((res) => setFactRunId(res.runId))
            .catch(() => setFactError("Fact-checking failed."));
    }, [id]);

    useEffect(() => {
        if (!factRunId) return;

        let alive = true;

        const poll = async () => {
            try {
                const result = await fetchFactCheckResult(factRunId);

                if (!alive) return;

                if (result) {
                    setFact(result);
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
    }, [factRunId]);

    if (!article) return <div className="page">Loading…</div>;

    return (
        <div className="page">
            <button type="button" className="backLink" onClick={() => navigate(-1)}>
                ← Back
            </button>

            <h2 style={{marginTop: 12}}>{article.title}</h2>

            <div className="meta">
                <a href={article.url} target="_blank" rel="noopener noreferrer" className="articleLink">
                    {article.source}
                </a>{" "}
                · <span>{article.author}</span> ·{" "}
                <span>
          {new Date(article.published_at).toLocaleString("de-DE", {
              day: "2-digit",
              month: "2-digit",
              year: "numeric",
              hour: "2-digit",
              minute: "2-digit",
              hour12: false,
          })}
        </span>
            </div>

            <div className="articleLayout">
                <div>
                    {article.image_url && (
                        <div className="heroWrap">
                            <img className="hero" src={article.image_url} />

                            <div className="c2paOverlay">
                                <C2PACard articleId={article.id} compact />
                            </div>
                        </div>
                    )}
                    <HighlightedArticleBody
                        html={article.content_html}
                        claims={fact?.claims}
                        articleId={article.id}
                    />
                </div>

                <div className="card">
                    <StyleCard articleId={article.id}/>

                    <FactCheckCard
                        id={article.id}
                        type="article"
                        data={fact}
                        runId={factRunId}
                        error={factError}
                    />

                    <AuthorExpertiseCard articleId={article.id}/>
                    <OwnershipPublisherCard articleId={article.id} source={article.source}/>
                    <C2PACard articleId={article.id}/>
                </div>
            </div>
        </div>
    );
}