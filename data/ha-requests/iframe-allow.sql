-- extract allow directives on iframes
--  779GB estimation, 16GB per crawl
-- CREATE TABLE `gcp-anonymized-project-name.privacysandbox.iframe-allow`
-- (
--   date DATE,
--   page STRING,
--   rank INTEGER,
--   directive STRING,
--   origin STRING
-- )
-- PARTITION BY date
-- CLUSTER BY
--   rank, page, directive

INSERT INTO `gcp-anonymized-project-name.privacysandbox.iframe-allow`
SELECT
  date,
  page,
  rank,
  SPLIT(TRIM(allow_attr), ' ')[OFFSET(0)] AS directive,
  TRIM(origin) AS origin,
FROM
  `httparchive.crawl.pages`,
  UNNEST(JSON_EXTRACT_ARRAY(custom_metrics.security.`iframe-allow-sandbox`)) AS iframeAttr,
  UNNEST(REGEXP_EXTRACT_ALL(JSON_EXTRACT_SCALAR(iframeAttr, '$.allow'), r'(?i)([^,;]+)')) AS allow_attr,
  UNNEST(  -- Directive may specify explicit origins or not.
    IF(
      ARRAY_LENGTH(SPLIT(TRIM(allow_attr), ' ')) = 1,  -- test if any explicit origin is provided
      [TRIM(allow_attr), ''],  -- if not, add a dummy empty origin to make the query work
      SPLIT(TRIM(allow_attr), ' '  -- if it is, split the different origins
      )
    )
  ) AS origin WITH OFFSET AS offset
WHERE
  date IN ('2021-03-01', '2021-04-01', '2021-05-01', '2021-06-01', '2021-07-01', '2021-08-01', '2021-09-01', '2021-10-01', '2021-11-01', '2021-12-01', '2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01', '2022-06-01', '2022-07-01', '2022-08-01', '2022-09-01', '2022-10-01', '2022-11-01', '2022-12-01', '2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01', '2023-06-01', '2023-07-01', '2023-08-01', '2023-09-01', '2023-10-01', '2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01', '2024-05-01', '2024-06-01', '2024-07-01', '2024-08-01', '2024-09-01', '2024-10-01', '2024-11-01', '2024-12-01', '2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01', '2025-07-01', '2025-08-01', '2025-09-01', '2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01', '2026-02-01', '2026-03-01', '2026-04-01') AND
  client = 'desktop' AND
  rank <= 100000 AND
  is_root_page AND
  offset > 0 AND ( -- do not retain the first part of the directive (as this is the directive name)
    ( LOWER(allow_attr) LIKE '%identity-credentials-get%' OR
      LOWER(allow_attr) LIKE '%interest-cohort%' OR
      LOWER(allow_attr) LIKE '%private-state-token%' OR
      LOWER(allow_attr) LIKE '%trust-token-redemption%' OR
      LOWER(allow_attr) LIKE '%storage-access%' OR
      LOWER(allow_attr) LIKE '%ch-ua%' OR
      LOWER(allow_attr) LIKE '%attribution-reporting%' OR
      LOWER(allow_attr) LIKE '%conversion-measurement%' OR
      LOWER(allow_attr) LIKE '%private-aggregation%' OR
      LOWER(allow_attr) LIKE '%join-ad-interest-group%' OR
      LOWER(allow_attr) LIKE '%run-ad-auction%' OR
      LOWER(allow_attr) LIKE '%shared-storage%' OR
      LOWER(allow_attr) LIKE '%browsing-topics%'
    ) -- can be several policies in the value of permission policy
  )