import {useEffect, useMemo, useState} from "react";
import {getFeed} from "../api/endpoints";
import type {FeedFilters, FeedResponse} from "../api/types";
import FilterBar from "../components/FilterBar";
import ArticleList from "../components/ArticleList";
import XPostList from "../components/XPostList";

export default function HomePage() {
    const [filters, setFilters] = useState<FeedFilters>({
        fact_checked: undefined,
        tone: [],
        content_type: [],
        publisher_type: [],
    });

    const [data, setData] = useState<FeedResponse>({articles: [], x_posts: []});
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);

    const stableFilters = useMemo(() => filters, [filters]);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setErr(null);

        getFeed(stableFilters)
            .then((d) => {
                if (!cancelled) setData(d);
            })
            .catch((e: unknown) => {
                if (!cancelled) setErr(e instanceof Error ? e.message : "Unknown error");
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, [stableFilters]);

    return (
        <div className="page">
            <header className="header">
                <h1>Personalized Media Experience</h1>
                <FilterBar value={filters} onChange={setFilters}/>
            </header>

            {err && <div className="error">Error: {err}</div>}
            {loading && <div className="hint">Loading…</div>}

            <div className="grid">
                <main className="main">
                    <ArticleList articles={data.articles}/>
                </main>

                <aside className="aside">
                    <XPostList posts={data.x_posts}/>
                </aside>
            </div>
        </div>
    );
}
