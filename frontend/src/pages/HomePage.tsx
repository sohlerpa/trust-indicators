import {useEffect, useMemo, useState} from "react";
import {getFeed} from "../api/endpoints";
import type {FeedFilters, FeedResponse} from "../api/types";
import FilterBar from "../components/FilterBar";
import ArticleList from "../components/ArticleList";
import XPostList from "../components/XPostList";
import DiversityScore from "../components/DiversityScore"
import ArticleIngest from "../components/ArticleIngest";

type FilterCounts = {
    tone: Record<string, number>;
    content_type: Record<string, number>;
    publisher_type: Record<string, number>;
};

function initCounts(keys: string[]) {
    return Object.fromEntries(keys.map(k => [k, 0])) as Record<string, number>;
}

export default function HomePage() {
    const [filters, setFilters] = useState<FeedFilters>({
        fact_checked: undefined,
        tone: [],
        content_type: [],
        publisher_type: [],
        no_false_facts: undefined,
        author_expert: undefined,
        c2pa_present: undefined,
    });

    const [data, setData] = useState<FeedResponse>({articles: [], x_posts: []});
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const [reloadToken, setReloadToken] = useState(0);

    const stableFilters = useMemo(() => filters, [filters]);

    const filtered_domains = useMemo(() => {
        const domains = data.articles
            .map(a => a.url)
            .filter((u): u is string => typeof u === "string" && u.length > 0)
            .map(u => {
                try {
                    return new URL(u).hostname.replace(/^www\./, "");
                } catch {
                    return null;
                }
            })
            .filter((d): d is string => d !== null);
        console.log("filtered_domains:", domains);
        return domains
    }, [data.articles]);


    const filterCounts = useMemo<FilterCounts>(() => {
        const tone = initCounts(["neutral", "analytical", "speculative", "conspiratorial", "sensational", "alarmist", "angry", "critical", "supportive", "skeptical", "humorous", "ironic", "promotional", "error"]);
        const content_type = initCounts(["news", "opinion", "analysis", "satire", "gossip", "review", "sponsored", "other", "error"]);
        const publisher_type = initCounts(["public", "private", "unknown"]);

        for (const a of data.articles) {
            const ti = a.trust_indicators;

            const t = ti.tone ?? "error";
            tone[t] = (tone[t] ?? 0) + 1;

            const ct = ti.content_type ?? "error";
            content_type[ct] = (content_type[ct] ?? 0) + 1;

            const pt = ti.publisher_type ?? "unknown";
            publisher_type[pt] = (publisher_type[pt] ?? 0) + 1;
        }

        return { tone, content_type, publisher_type };
    }, [data.articles]);

    useEffect(() => {
        let cancelled = false;
        setLoading(true);
        setErr(null);

        getFeed(stableFilters)
            .then((d) => {
                console.log("RAW FEED RESPONSE:", d);
                console.log(
                    "RAW ARTICLE URLS:",
                    d.articles.map(a => a.url)
                );
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
    }, [stableFilters, reloadToken]);

    return (
        <div className="page">
            <div className="stack">
                <header className="header">
                    <h1>Personalized Media Experience</h1>
                    <FilterBar value={filters} onChange={setFilters} counts={filterCounts} />
                </header>

                <div className="grid">
                    <main className="main stack">
                        <ArticleIngest onInserted={() => setReloadToken(t => t + 1)} />

                        {err && <div className="error">Error: {err}</div>}
                        {loading && <div className="hint">Loading…</div>}

                        <DiversityScore domains={filtered_domains} />

                        <ArticleList articles={data.articles}/>
                    </main>

                    <aside className="aside">
                        <XPostList posts={data.x_posts}/>
                    </aside>
                </div>
            </div>
        </div>
    );
}
