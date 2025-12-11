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