WITH hostRanked AS (
  SELECT
    *,
    ROW_NUMBER() OVER (
      PARTITION BY date 
      ORDER BY total_without_ua_client_hints DESC
    ) AS date_rank
  FROM (
    SELECT
      *,
      (grand_total_apis - ua_client_hints_total) AS total_without_ua_client_hints
    FROM (
  SELECT 
    date,
    host,
    SUM(IF(attribution, 1, 0)) AS attribution_total,
    SUM(IF(fedcm, 1, 0)) AS fedcm_total,
    SUM(IF(fenced_frames, 1, 0)) AS fenced_frames_total,
    SUM(IF(floc, 1, 0)) AS floc_total,
    SUM(IF(private_aggregation, 1, 0)) AS private_aggregation_total,
    SUM(IF(private_state_tokens, 1, 0)) AS private_state_tokens_total,
    SUM(IF(protected_audience, 1, 0)) AS protected_audience_total,
    SUM(IF(shared_storage, 1, 0)) AS shared_storage_total,
    SUM(IF(storage_access, 1, 0)) AS storage_access_total,
    SUM(IF(topics, 1, 0)) AS topics_total,
    SUM(IF(ua_client_hints, 1, 0)) AS ua_client_hints_total,
    SUM(total_apis) AS grand_total_apis
    FROM `gcp-anonymized-project-name.privacysandbox.apis`
    WHERE
    date IN ('2023-09-01', '2024-09-01', '2025-09-01')
  GROUP BY
    date, host
  )
  )
)

SELECT 
  *
FROM hostRanked
WHERE date_rank <= 100
ORDER BY date, total_without_ua_client_hints DESC;


