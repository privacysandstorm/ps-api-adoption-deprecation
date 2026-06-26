-- query custom metric for cookies - only for crawls after June 2024
-- time and scan size (estimate of 1.97TB)
-- results dump or output

-- CREATE TABLE `gcp-anonymized-project-name.privacysandbox.cookies-custom-metrics`
-- (
--   date DATE,
--   page STRING,
--   rank INTEGER,
--   firstParty BOOL,
--   name STRING,
--   domain STRING,
--   path STRING,
--   httpOnly STRING,
--   secure STRING,
--   session STRING,
--   sameSite STRING,
--   sameParty STRING,
--   partitionKey STRING,
--   partitionKeyOpaque STRING
-- )
-- PARTITION BY date
-- CLUSTER BY
--   rank, page, firstParty

INSERT INTO `gcp-anonymized-project-name.privacysandbox.cookies-custom-metrics`
SELECT
  date,
  page,
  rank,
  ENDS_WITH(NET.HOST(page), '.' || NET.REG_DOMAIN(JSON_VALUE(cookie.domain))) AS firstParty,
  JSON_VALUE(cookie.name) AS name,
  JSON_VALUE(cookie.domain) AS domain,
  JSON_VALUE(cookie.path) AS path,
  JSON_VALUE(cookie.httpOnly) AS httpOnly,
  JSON_VALUE(cookie.secure) AS secure,
  JSON_VALUE(cookie.session) AS session,
  JSON_VALUE(cookie.sameSite) AS sameSite,
  JSON_VALUE(cookie.sameParty) AS sameParty,
  NULLIF(TO_JSON_STRING(cookie.partitionKey), 'null') AS partitionKey,
  NULLIF(TO_JSON_STRING(cookie.partitionKeyOpaque), 'null') AS partitionKeyOpaque
FROM
  `httparchive.crawl.pages`,
  UNNEST(JSON_EXTRACT_ARRAY(custom_metrics.cookies)) AS cookie
WHERE
  date IN ('2024-06-01', '2024-07-01', '2024-08-01', '2024-09-01', '2024-10-01', '2024-11-01', '2024-12-01', '2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01', '2025-07-01', '2025-08-01', '2025-09-01', '2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01', '2026-02-01', '2026-03-01', '2026-04-01') AND
  client = 'desktop' AND
  rank <= 100000 AND
  is_root_page
