import {useEffect, useState} from "react";
import {Link, useParams} from "react-router-dom";
import {getArticle} from "../api/endpoints";
import type {ArticleBase} from "../api/types";
import FactCheckCard from "../components/FactCheckCard";
import AuthorExpertiseCard from "../components/AuthorExpertiseCard";
import StyleCard from "../components/StyleCard";
import C2PACard from "../components/C2PACard";
import OwnershipPublisherCard from "../components/PublisherOwnershipCars";

export default function ArticlePage() {
    const {id} = useParams();
    const [article, setArticle] = useState<ArticleBase | null>(null);

    useEffect(() => {
        if (!id) return;
        getArticle(id).then(setArticle);
    }, [id]);

    if (!article) return <div className="page">Loading…</div>;

    return (
        <div className="page">
            <Link to="/">← Back</Link>

            <h2 style={{marginTop: 12}}>
                {article.title}
            </h2>

            <div className="meta">
                <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="articleLink"
                >
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
                        <img className="hero" src={article.image_url} alt="" />
                    )}

                    <article
                        className="articleBody card"
                        dangerouslySetInnerHTML={{__html: article.content_html}}
                    />
                </div>

                <div className="card">
                    <StyleCard articleId={article.id}/>
                    <FactCheckCard id={article.id} type={"article"}/>
                    <AuthorExpertiseCard articleId={article.id}/>
                    <OwnershipPublisherCard articleId={article.id} source={article.source}/>
                    <C2PACard articleId={article.id}/>
                </div>
            </div>
        </div>
    );
}