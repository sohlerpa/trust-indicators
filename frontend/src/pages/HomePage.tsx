import {useEffect, useMemo, useState} from "react";
import {useSearchParams} from "react-router-dom";
import {getFeed} from "../api/endpoints";
import type {FeedFilters, FeedResponse} from "../api/types";
import FilterBar from "../components/FilterBar";
import ArticleList from "../components/ArticleList";
import XPostList from "../components/XPostList";
import DiversityScore from "../components/DiversityScore";
import ArticleIngest from "../components/ArticleIngest";

type FilterCounts = {
    tone: Record<string, number>;
    content_type: Record<string, number>;
    publisher_type: Record<string, number>;
    c2pa_present: { true: number; false: number };
    has_false_facts: { true: number; false: number };
    author_expert: { field_expert: number; not_field_expert: number; unknown: number };
};

function initCounts(keys: string[]) {
    return Object.fromEntries(keys.map(k => [k, 0])) as Record<string, number>;
}

function parseBoolTri(v: string | null): boolean | undefined {
    if (v === null) return undefined;
    if (v === "true") return true;
    if (v === "false") return false;
    return undefined;
}

function readFiltersFromSearchParams(sp: URLSearchParams): FeedFilters {
    const fact_checked = parseBoolTri(sp.get("fact_checked"));

    const tone = sp.getAll("tone");
    const content_type = sp.getAll("content_type");
    const publisher_type = sp.getAll("publisher_type");

    const no_false_facts = parseBoolTri(sp.get("no_false_facts"));
    const c2pa_present = parseBoolTri(sp.get("c2pa_present"));
    console.log("c2pa_present: ", c2pa_present)

    const author_expert_raw = sp.get("author_expert");
    const author_expert =
        author_expert_raw === "field_expert" ||
        author_expert_raw === "not_field_expert" ||
        author_expert_raw === "unknown"
            ? author_expert_raw
            : undefined;

    return {
        fact_checked,
        tone,
        content_type,
        publisher_type,
        no_false_facts,
        author_expert,
        c2pa_present,
    };
}

function writeFiltersToSearchParams(filters: FeedFilters): URLSearchParams {
    const p = new URLSearchParams();

    if (filters.fact_checked !== undefined) p.set("fact_checked", String(filters.fact_checked));
    for (const t of filters.tone ?? []) p.append("tone", t);
    for (const ct of filters.content_type ?? []) p.append("content_type", ct);
    for (const pt of filters.publisher_type ?? []) p.append("publisher_type", pt);

    if (filters.no_false_facts !== undefined) p.set("no_false_facts", String(filters.no_false_facts));
    if (filters.author_expert !== undefined) p.set("author_expert", filters.author_expert);
    if (filters.c2pa_present !== undefined) p.set("c2pa_present", String(filters.c2pa_present));

    return p;
}

export default function HomePage() {
    const [searchParams, setSearchParams] = useSearchParams();

    // init from URL once
    const [filters, setFilters] = useState<FeedFilters>(() => readFiltersFromSearchParams(searchParams));

    const [data, setData] = useState<FeedResponse>({articles: [], x_posts: []});
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const [reloadToken, setReloadToken] = useState(0);

    // Keep filters in sync when user navigates Back/Forward (URL changes)
    useEffect(() => {
        setFilters(readFiltersFromSearchParams(searchParams));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchParams.toString()]);

    // Write filters to URL whenever they change
    useEffect(() => {
        const next = writeFiltersToSearchParams(filters);
        const nextStr = next.toString();
        const curStr = searchParams.toString();

        if (nextStr !== curStr) {
            // replace so we don't spam history entries when toggling chips
            setSearchParams(next, {replace: true});
        }
    }, [filters, searchParams, setSearchParams]);

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
        return domains;
    }, [data.articles]);

    const filterCounts = useMemo<FilterCounts>(() => {
        const tone = initCounts([
            "neutral", "analytical", "speculative", "conspiratorial", "sensational", "alarmist",
            "angry", "critical", "supportive", "skeptical", "humorous", "ironic", "promotional", "error"
        ]);
        const content_type = initCounts(["news", "opinion", "analysis", "satire", "gossip", "review", "sponsored", "other", "error"]);
        const publisher_type = initCounts(["public", "private", "unknown"]);
        const c2pa_present = { true: 0, false: 0 };
        const author_expert = { field_expert: 0, not_field_expert: 0, unknown: 0 };
        const has_false_facts = { true: 0, false: 0 };

        for (const a of data.articles) {
            const ti = a.trust_indicators;

            const t = ti.tone ?? "error";
            tone[t] = (tone[t] ?? 0) + 1;

            const ct = ti.content_type ?? "error";
            content_type[ct] = (content_type[ct] ?? 0) + 1;

            const pt = ti.publisher_type ?? "unknown";
            publisher_type[pt] = (publisher_type[pt] ?? 0) + 1;

            const v = ti.c2pa_present; // boolean | null | undefined
            if (v === true) c2pa_present.true += 1;
            else if (v === false) c2pa_present.false += 1;

            const ae = ti.author_expertise?.label ?? "unknown";
            if (ae === "field_expert") author_expert.field_expert += 1;
            else if (ae === "not_field_expert") author_expert.not_field_expert += 1;
            else author_expert.unknown += 1;

            const hf = ti.has_false_facts; // boolean | null | undefined
            if (hf === true) has_false_facts.true += 1;
            else if (hf === false) has_false_facts.false += 1;
        }

        return {tone, content_type, publisher_type, c2pa_present, author_expert, has_false_facts};
    }, [data.articles]);

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
    }, [stableFilters, reloadToken]);

    return (
        <div className="page">
            <div className="stack">
                <header className="header">
                    <h1>Personalized Media Experience</h1>
                    <FilterBar value={filters} onChange={setFilters} counts={filterCounts}/>
                </header>

                <div className="grid">
                    <main className="main stack">
                        <div className="topRow">
                            <DiversityScore domains={filtered_domains} />
                            <ArticleIngest onInserted={() => setReloadToken(t => t + 1)} />
                        </div>

                        {err && <div className="error">Error: {err}</div>}
                        {loading && <div className="hint">Loading…</div>}

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