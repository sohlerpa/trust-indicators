import {Link} from "react-router-dom";
import type {ArticleSummary} from "../api/types";

export default function ArticleList({articles}: { articles: ArticleSummary[] }) {
    return (
        <div className="card">
            <h3>Articles</h3>
            <div className="list">
                {articles.map((a) => (
                    <Link key={a.id} to={`/articles/${a.id}`} className="item">
                        {a.image_url && <img className="thumb" src={a.image_url} alt=""/>}
                        <div className="itemBody">
                            <div className="itemTitle">
                                {a.title}
                                <span className={`badge ${a.trust_indicators.badge}`} title={a.trust_indicators.badge}/>
                            </div>
                            <div className="metaSmall">
                                {a.source} · {new Date(a.published_at).toLocaleString()}
                            </div>
                            <div>
                                {a.preview && (
                                    <p className="article-preview">{a.preview}</p>
                                )}
                            </div>
                        </div>
                    </Link>
                ))}
                {articles.length === 0 && <div className="hint">No articles match the current filters.</div>}
            </div>
        </div>
    );
}