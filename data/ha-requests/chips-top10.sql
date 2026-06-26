SELECT
  name,
  domain,
  ROUND(COUNT(DISTINCT NET.HOST(page)) / (
    SELECT
      (COUNT(DISTINCT NET.HOST(page)))
    FROM
      `gcp-anonymized-project-name.privacysandbox.cookies-custom-metrics`
    WHERE
      date = '2026-04-01' AND
      firstParty = FALSE AND
      partitionKey IS NOT NULL
  ) * 100,2) AS percentWebsites
FROM
  `gcp-anonymized-project-name.privacysandbox.cookies-custom-metrics`
WHERE
  date = '2026-04-01' AND
  firstParty = FALSE AND
  partitionKey IS NOT NULL
GROUP BY
  name, domain
ORDER BY
  percentWebsites DESC
LIMIT
  10

-- name	domain	percentWebsites
-- cto_bundle	.criteo.com	43.91
-- audit_p	.rubiconproject.com	34.32
-- khaos_p	.rubiconproject.com	34.32
-- receive-cookie-deprecation	.rubiconproject.com	29.88
-- ts	.creativecdn.com	29.02
-- VP	.contextweb.com	22.15
-- pamuid2	.a-mo.net	21.09
-- psd_amuid2	.sync.a-mo.net	20.28
-- pb_rtb_ev_part	.contextweb.com	19.93
-- server_tracking_bdsp_uid	.tracookiepixel.xyz	18.88


SELECT
  name,
  ROUND(COUNT(DISTINCT NET.HOST(page)) / (
    SELECT
      (COUNT(DISTINCT NET.HOST(page)))
    FROM
      `gcp-anonymized-project-name.privacysandbox.cookies-custom-metrics`
    WHERE
      date = '2026-04-01' AND
      firstParty = TRUE AND
      partitionKey IS NOT NULL
  ) *100,2) AS percentWebsites
FROM
  `gcp-anonymized-project-name.privacysandbox.cookies-custom-metrics`
WHERE
  date = '2026-04-01' AND
  firstParty = TRUE AND
  partitionKey IS NOT NULL
GROUP BY
  name
ORDER BY
  percentWebsites DESC
LIMIT
  10

-- name	percentWebsites
-- cf_clearance	90.37
-- __attn_eat_id	3.11
-- csrf_token	0.62
-- ds2	0.6
-- fp_token_7c6a6574-f011-4c9a-abdd-9894a102ccef	0.6
-- __cfwaitingroom	0.57
-- pi	0.53
-- yashr	0.48
-- tag_user_id	0.4
-- tag_session	0.4