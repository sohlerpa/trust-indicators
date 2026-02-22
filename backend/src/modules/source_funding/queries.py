from sqlalchemy import text

# "Which owners together own >70% of a company behind a domain?"
GET_DOMAIN_OWNERS = text("""
WITH owner_data AS (
    SELECT 
        o.name,
        co.ownership_percent
    FROM domains d
    JOIN companies c ON d.company_id = c.id
    JOIN company_ownership co ON co.company_id = c.id
    JOIN owners o ON o.id = co.owner_id
    WHERE d.domain = :domain
    ORDER BY co.ownership_percent DESC
),
cumulative AS (
    SELECT
        name,
        ownership_percent,
        SUM(ownership_percent) OVER (ORDER BY ownership_percent DESC) AS cumulative_sum
    FROM owner_data
)
SELECT name, ownership_percent
FROM cumulative
WHERE cumulative_sum <= 70
   OR ownership_percent = (
        SELECT ownership_percent
        FROM cumulative
        WHERE cumulative_sum > 70
        ORDER BY cumulative_sum
        LIMIT 1
   );
""")

# Which owners dominate my feed?
GET_FEED_OWNERSHIP = text("""
WITH feed_domains AS (
    SELECT unnest(:domains) AS domain
),
joined AS (
    SELECT
        o.name AS owner_name,
        co.ownership_percent
    FROM feed_domains fd
    JOIN domains d          ON d.domain = fd.domain
    JOIN company_ownership co ON co.company_id = d.company_id
    JOIN owners o           ON o.id = co.owner_id
)
SELECT owner_name, SUM(ownership_percent) AS total_influence
FROM joined
GROUP BY owner_name
ORDER BY total_influence DESC;
""")

# Retrieve publisher type and country for a domain.
GET_DOMAIN_PUBLISHER_TYPE = text("""
SELECT
    c.publisherType AS publisher_type,
    c.country       AS country
FROM domains d
JOIN companies c ON c.id = d.company_id
WHERE d.domain = :domain;
""")
