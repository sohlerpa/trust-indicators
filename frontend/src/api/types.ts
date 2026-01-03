export type Badge = "green" | "orange" | "red";
export type PublisherType = "public" | "private" | "unknown";

export type TrustIndicators = {
    badge: Badge;
    fact_checked: boolean;
    tone?: string | null;
    content_type?: string | null;
    publisher_type: PublisherType;
    c2pa_present: boolean;
};

export type ArticleSummary = {
    id: string;
    title: string;
    source: string;
    published_at: string;
    image_url?: string | null;
    trust_indicators: TrustIndicators;
};

export type ArticleDetail = ArticleSummary & {
    url?: string | null;
    author?: string | null;
    content: string;
};

export type XPost = {
    id: string;
    handle: string;
    display_name: string;
    text: string;
    created_at: string;
    indicators: TrustIndicators;
};

export type FeedResponse = {
    articles: ArticleSummary[];
    x_posts: XPost[];
};

export type FeedFilters = {
    fact_checked?: boolean;
    tone?: string[];
    content_type?: string[];
    publisher_type?: string[];
};