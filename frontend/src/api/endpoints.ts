import {apiGet, apiPost} from "./client";
import type {FeedFilters, FeedResponse, ArticleDetail, XPost, ArticleBase, FactCheckTrust, C2PATrust, OwnershipTrust, PublisherTrust, StyleTrust, AuthorExpertiseTrust} from "./types";

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
    return apiGet<ArticleBase>(`/api/articles/${id}`);
}

export function getArticleStyle(id: string) {
    return apiGet<StyleTrust>(`/api/articles/${id}/trust/style`);
}

export function getArticleFactCheck(id: string) {
    return apiGet<FactCheckTrust>(`/api/articles/${id}/trust/fact-check`);
}

export function getArticleAuthor(id: string) {
    return apiGet<AuthorExpertiseTrust>(`/api/articles/${id}/trust/author`);
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