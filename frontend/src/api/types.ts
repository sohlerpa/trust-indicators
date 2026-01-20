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
    articleId: string;
    generatedAt: string; // ISO date
    stats: {
        extractedClaims: number;   // total from LLM extraction
        checkedClaims: number;     // claims with evidence (returned)
        droppedClaims: number;     // extracted - checked
        dropReasons: {
            noEvidence: number;      // fact_checks=[]
            keywordExtractionFailed?: number;
            assertionFailed?: number;
        };
    };
    claims: FactCheckTrustClaim[]; // only the checked ones (with evidence)
};

export type FactCheckTrustClaim = {
    id: string; // stable id for React keys / tooltip mapping (you generate it)
    claimText: string;     // normalized claim text (LLM)
    sourceText: string;    // exact substring from plain_text (for display)
    startChar: number;     // start offset in plain_text
    endChar: number;       // end offset in plain_text
    reason?: string;       // why extracted (optional)
    query: {
        primary: string;
        alternatives: string[];
    };
    verdict: "true" | "false" | "unclear";
    confidence: number;    // 0..1
    summary: string;       // 1-2 sentences
    reasoning: string;     // short, evidence-based
    sources: Array<{
        publisher?: string;
        publisherSite?: string;
        title?: string;
        url?: string;
        reviewDate?: string;
        textualRating?: string;
        languageCode?: string;
    }>;
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
    url: string;
    text: string;
    mediaUrl: string;
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

export type IngestArticleResponse = {
    id: string
};