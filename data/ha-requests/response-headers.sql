-- extract cookies and permissions (and api_headers) set from response_headers requests
-- 1.37 TB total vs 13GB per crawl
-- CREATE TABLE `gcp-anonymized-project-name.privacysandbox.response-headers`
-- (
--   date DATE,
--   page STRING,
--   rank INTEGER,
--   host STRING,
--   url STRING,
--   is_main_document BOOL,
--   type STRING,
--   header_name STRING,
--   header_value STRING
-- )
-- PARTITION BY date
-- CLUSTER BY
--   rank, page, host, header_name

INSERT INTO `gcp-anonymized-project-name.privacysandbox.response-headers`
SELECT
  date,
  page,
  rank,
  NET.HOST(url) AS host,
  url,
  is_main_document,
  type,
  response_headers.name AS header_name,
  response_headers.value AS header_value,
FROM
  `httparchive.crawl.requests`,
  UNNEST(response_headers) AS response_headers
WHERE
  date IN ('2021-03-01', '2021-04-01', '2021-05-01', '2021-06-01', '2021-07-01', '2021-08-01', '2021-09-01', '2021-10-01', '2021-11-01', '2021-12-01', '2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01', '2022-06-01', '2022-07-01', '2022-08-01', '2022-09-01', '2022-10-01', '2022-11-01', '2022-12-01', '2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01', '2023-06-01', '2023-07-01', '2023-08-01', '2023-09-01', '2023-10-01', '2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01', '2024-05-01', '2024-06-01', '2024-07-01', '2024-08-01', '2024-09-01', '2024-10-01', '2024-11-01', '2024-12-01', '2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01', '2025-07-01', '2025-08-01', '2025-09-01', '2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01', '2026-02-01', '2026-03-01', '2026-04-01') AND
  client = 'desktop' AND
  rank <= 100000 AND
  is_root_page AND (
    LOWER(response_headers.name) LIKE '%set-cookie%' OR
    (LOWER(response_headers.name) LIKE '%permissions-policy%' AND (
      LOWER(response_headers.value) LIKE '%identity-credentials-get%' OR
      LOWER(response_headers.value) LIKE '%interest-cohort%' OR
      LOWER(response_headers.value) LIKE '%private-state-token%' OR
      LOWER(response_headers.value) LIKE '%trust-token-redemption%' OR
      LOWER(response_headers.value) LIKE '%storage-access%' OR
      LOWER(response_headers.value) LIKE '%ch-ua%' OR
      LOWER(response_headers.value) LIKE '%attribution-reporting%' OR
      LOWER(response_headers.value) LIKE '%conversion-measurement%' OR
      LOWER(response_headers.value) LIKE '%private-aggregation%' OR
      LOWER(response_headers.value) LIKE '%join-ad-interest-group%' OR
      LOWER(response_headers.value) LIKE '%run-ad-auction%' OR
      LOWER(response_headers.value) LIKE '%shared-storage%' OR
      LOWER(response_headers.value) LIKE '%browsing-topics%' )
    ) OR -- can be several policies in the value of permission policy
    LOWER(response_headers.name) LIKE '%set-login%' OR
    (LOWER(response_headers.name) LIKE '%sec-fetch-dest%' AND LOWER(response_headers.value) LIKE '%fencedframe%') OR
    (LOWER(response_headers.name) LIKE '%supports-loading-mode%' AND LOWER(response_headers.value) LIKE '%fenced-frame%') OR
    LOWER(response_headers.name) LIKE '%sec-private-state-token%' OR
    LOWER(response_headers.name) LIKE '%sec-redemption-record%' OR
    LOWER(response_headers.name) LIKE '%sec-fetch-storage-access%' OR
    LOWER(response_headers.name) LIKE '%activate-storage-access%' OR
    LOWER(response_headers.name) LIKE '%accept-ch%' OR
    LOWER(response_headers.name) LIKE '%critical-ch%' OR
    LOWER(response_headers.name) LIKE '%delegate-ch%' OR
    LOWER(response_headers.name) LIKE '%sec-ch-ua%' OR
    LOWER(response_headers.name) LIKE '%attribution-reporting%' OR
    LOWER(response_headers.name) LIKE '%ad-auction%' OR
    LOWER(response_headers.name) LIKE '%x-fledge-bidding-signals-format-version%' OR
    LOWER(response_headers.name) LIKE '%data-version%' OR
    LOWER(response_headers.name) LIKE '%shared-storage%' OR
    LOWER(response_headers.name) LIKE '%browsing-topics%'
  )