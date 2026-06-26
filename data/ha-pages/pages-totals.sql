-- Query only starting in 2021-03-01 (first detection of kfeature in usage, so nothing extracted from 2020-01-01 to 2021-02-01)
-- 8min 35sec 167GB
-- dumps into pages-totals.csv

-- CREATE TABLE `gcp-anonymized-project-name.privacysandbox.pages-totals`
-- (
--   date DATE,
--   client STRING,
--   rank_grouping INTEGER,
--   is_root_page BOOL,
--   total_pages INTEGER
-- )
-- PARTITION BY date
-- CLUSTER BY
--   client, rank_grouping

INSERT INTO `gcp-anonymized-project-name.privacysandbox.pages-totals`
SELECT
  date,
  client,
  rank_grouping,
  is_root_page,
  COUNT(DISTINCT page) AS total_pages,
FROM
  `httparchive.crawl.pages`,
  UNNEST([1000, 5000, 10000, 50000, 100000]) AS rank_grouping
WHERE
  rank <= rank_grouping AND
  date IN ('2021-03-01', '2021-04-01', '2021-05-01', '2021-06-01', '2021-07-01', '2021-08-01', '2021-09-01', '2021-10-01', '2021-11-01', '2021-12-01', '2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01', '2022-06-01', '2022-07-01', '2022-08-01', '2022-09-01', '2022-10-01', '2022-11-01', '2022-12-01', '2023-01-01', '2023-02-01', '2023-03-01', '2023-04-01', '2023-05-01', '2023-06-01', '2023-07-01', '2023-08-01', '2023-09-01', '2023-10-01', '2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01', '2024-04-01', '2024-05-01', '2024-06-01', '2024-07-01', '2024-08-01', '2024-09-01', '2024-10-01', '2024-11-01', '2024-12-01', '2025-01-01', '2025-02-01', '2025-03-01', '2025-04-01', '2025-05-01', '2025-06-01', '2025-07-01', '2025-08-01', '2025-09-01', '2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01', '2026-02-01', '2026-03-01', '2026-04-01')
GROUP BY date, client, rank_grouping, is_root_page
ORDER BY date ASC, client, rank_grouping ASC