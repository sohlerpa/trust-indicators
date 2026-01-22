import {apiGet, apiPost} from "./client";
import type {
    ArticleBase,
    AuthorExpertiseTrust,
    C2PATrust,
    FeedFilters,
    FeedResponse,
    IngestArticleResponse,
    OwnershipTrust,
    PublisherTrust,
    StyleTrust,
    XPost
} from "./types";

function qs(filters: FeedFilters): string {
    const p = new URLSearchParams();

    if (filters.fact_checked !== undefined) p.set("fact_checked", String(filters.fact_checked));
    for (const t of filters.tone ?? []) p.append("tone", t);
    for (const ct of filters.content_type ?? []) p.append("content_type", ct);
    for (const pt of filters.publisher_type ?? []) p.append("publisher_type", pt);
    if (filters.no_false_facts !== undefined) p.set("no_false_facts", String(filters.no_false_facts));
    if (filters.author_expert !== undefined) p.set("author_expert", filters.author_expert);
    if (filters.c2pa_present !== undefined) p.set("c2pa_present", String(filters.c2pa_present));


    const s = p.toString();
    return s ? `?${s}` : "";
}

export function getFeed(filters: FeedFilters) {
    return apiGet<FeedResponse>(`/api/feed${qs(filters)}`);
}

export function getArticle(id: string) {
    return apiGet<ArticleBase>(`/api/articles/${id}`);
}

export function getArticleStyle(id: string) {
    return apiGet<StyleTrust>(`/api/articles/${id}/trust/style`);
}

export async function getArticleFactCheck(id: string) {
    const res = await fetch(
        `/api/articles/${id}/trust/fact-check`,
        { method: "POST" }
    );

    if (!res.ok) {
        throw new Error("Fact check failed");
    }

    return res.json(); // { runId }
}

export function getArticleAuthor(id: string) {
    return apiGet<AuthorExpertiseTrust>(`/api/articles/${id}/trust/author`);
}

export async function startAuthorExpertise(id: string) {
    const res = await fetch(
        `/api/articles/${id}/trust/author`,
        { method: "POST" }
    );

    if (!res.ok) {
        throw new Error("Author check failed");
    }

    return res.json(); // { runId }
}

export function getArticlePublisher(id: string) {
    return apiGet<PublisherTrust>(`/api/articles/${id}/trust/publisher`);
}

export function getArticleOwners(id: string) {
    return apiGet<OwnershipTrust>(`/api/articles/${id}/trust/owners`);
}

export function getArticleC2PA(id: string) {
    return apiGet<C2PATrust>(`/api/articles/${id}/trust/c2pa`);
}

export function getXPosts() {
    return apiGet<XPost[]>(`/api/xposts`);
}

export async function getXPostFactCheck(id: string) {
    const res = await fetch(
        `/api/xposts/${id}/fact-check`,
        { method: "POST" }
    );

    if (!res.ok) {
        throw new Error("Fact check failed");
    }

    return res.json();
}

export type Progress = {
    step: string;
    progress: number;
};

export function getProgress(runId: string) {
    return apiGet<Progress>(`/api/progress/${runId}`);
}

export type DiversityRow = {
    owner: string;
    influence: number;
};

export function getFeedDiversity(domains: string[]) {
    return apiPost<DiversityRow[]>(
        "/api/feed/diversity",
        {
            method: "POST",
            body: JSON.stringify(domains),
        }
    );
}

export async function ingestArticleFromUrl(url: string): Promise<IngestArticleResponse> {
    return apiPost<IngestArticleResponse>(
        "/api/articles/ingest",
        {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url}),
        }
    );
}

export async function startArticleFactCheck(id: string): Promise<{ runId: string }> {
    const res = await fetch(`/api/articles/${id}/trust/fact-check`, {method: "POST"});
    if (!res.ok) throw new Error("Fact check failed");
    return res.json();
}

export async function fetchFactCheckResult(runId: string) {
    const res = await fetch(`/api/fact-check/result/${runId}`);
    if (!res.ok) return null;
    return res.json();
}