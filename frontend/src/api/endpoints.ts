import {apiGet, apiPost} from "./client";
import type {FeedFilters, FeedResponse, ArticleDetail, XPost} from "./types";

function qs(filters: FeedFilters): string {
    const p = new URLSearchParams();

    if (filters.fact_checked !== undefined) p.set("fact_checked", String(filters.fact_checked));
    for (const t of filters.tone ?? []) p.append("tone", t);
    for (const ct of filters.content_type ?? []) p.append("content_type", ct);
    for (const pt of filters.publisher_type ?? []) p.append("publisher_type", pt);

    const s = p.toString();
    return s ? `?${s}` : "";
}

export function getFeed(filters: FeedFilters) {
    return apiGet<FeedResponse>(`/api/feed${qs(filters)}`);
}

export function getArticle(id: string) {
    return apiGet<ArticleDetail>(`/api/articles/${id}`);
}

export function getXPosts() {
    return apiGet<XPost[]>(`/api/xposts`);
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