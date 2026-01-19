export type Badge = "green" | "orange" | "red";
export type PublisherType = "public" | "private" | "unknown";

export type TrustIndicators = {
    badge: Badge;
    fact_checked: boolean;
    tone?: string | null;
    content_type?: string | null;
    tone_type_rationale?: string | null;
    publisher_type: PublisherType;
    publisher_country?: string;
    c2pa_present: boolean;
    owners?: OwnerInfo[];
    c2pa_info?: ImageProvenance[];
    author_expertise?: AuthorExpertise;
};

export type OwnerInfo = {
    owner: string;
    percent: number;
};

export type ImageProvenance = {
    src: string;
    c2pa_present: boolean;
    issuer: string | null;
    title: string | null;
    is_ai_generated: boolean;
}

export type AuthorExpertise = {
    author: string | null;
    article_url: string | null;
    publisher_domain: string | null;
    field: string | null;
    label: string | null;
    confidence: number;
    explanation: string | null;
}

export type ArticleSummary = {
    id: string;
    title: string;
    preview: string;
    url: string;
    source: string;
    published_at: string;
    image_url?: string | null;
    trust_indicators: TrustIndicators;
};

export type ArticleDetail = {
    id: string;
    title: string;
    preview: string;
    url: string;
    source: string;
    published_at: string;
    image_url?: string | null;
    author?: string | null;
    content_html: string;
};

export type ArticleBase = {
    id: string;
    title: string;
    preview: string;
    url: string;
    source: string;
    published_at: string;
    image_url?: string | null;
    author?: string | null;
    content_html: string;
};

export type StyleTrust = {
    tone: string | null;
    content_type: string | null;
    tone_type_rationale: string | null;
};

export type FactCheckTrust = {
    fact_checked: boolean;
};

export type AuthorExpertiseTrust = AuthorExpertise;

export type PublisherTrust = {
    publisher_type: PublisherType;
    publisher_country?: string;
};

export type OwnershipTrust = {
    owners?: OwnerInfo[];
};

export type C2PATrust = {
    c2pa_present: boolean;
    c2pa_info?: ImageProvenance[];
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