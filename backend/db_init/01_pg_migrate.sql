CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    isPublisher BOOLEAN NOT NULL,
    publisherType TEXT,   -- private, public, government
    country TEXT
);

CREATE TABLE IF NOT EXISTS domains (
    id SERIAL PRIMARY KEY,
    domain TEXT NOT NULL UNIQUE,
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS owners (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    owner_type TEXT NOT NULL,   -- individual, corporation, bank, investment_firm, foundation, government, ...
    country TEXT
);

CREATE TABLE IF NOT EXISTS company_ownership (
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    owner_id INT NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
    ownership_percent NUMERIC,
    PRIMARY KEY (company_id, owner_id)
);

CREATE TABLE articles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    author TEXT,
    published_at TIMESTAMP NOT NULL,
    image_url TEXT,
    preview TEXT,
    content_html TEXT,
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE article_llm_analysis (
    article_id TEXT PRIMARY KEY
        REFERENCES articles(id) ON DELETE CASCADE,

    badge TEXT NOT NULL DEFAULT 'grey',
    fact_checked BOOLEAN,
    tone TEXT,
    content_type TEXT,
    tone_type_rationale TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE article_c2pa_assets (
    id SERIAL PRIMARY KEY,

    article_id TEXT NOT NULL
        REFERENCES articles(id) ON DELETE CASCADE,

    src TEXT NOT NULL,
    c2pa_present BOOLEAN NOT NULL,
    issuer TEXT,
    title TEXT,
    is_ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);