
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

SELECT 
  host,
  COUNT(0) AS freq
FROM `gcp-anonymized-project-name.privacysandbox.response-headers`
WHERE
  date = '2026-04-01'
  AND (
    LOWER(header_name) LIKE '%accept-ch%' OR
    LOWER(header_name) LIKE '%critical-ch%' OR
    LOWER(header_name) LIKE '%delegate-ch%' OR
    LOWER(header_name) LIKE '%sec-ch-ua%' )
GROUP BY
  host
ORDER BY
  freq DESC
LIMIT 10

-- host	freq
-- pixel.tapad.com	393876
-- securepubads.g.doubleclick.net	289781
-- ib.adnxs.com	126350
-- fundingchoicesmessages.google.com	96175
-- secure.adnxs.com	67082
-- c1.adform.net	41815
-- bh.contextweb.com	29944
-- bat.bing.com	24012
-- mc.yandex.com	23761
-- ads.yieldmo.com	23268


SELECT 
  host,
  base_script,
  ROUND(COUNT(DISTINCT page)/55287 * 100,2) AS pages
FROM (
  SELECT
    host,
    page,
    REGEXP_EXTRACT(script_name, r'^([^?]*)') AS base_script
  FROM `gcp-anonymized-project-name.privacysandbox.apis`
  WHERE
  date = '2026-04-01'
  AND ua_client_hints
)
GROUP BY
  host, base_script
ORDER BY
  pages DESC
LIMIT 10


-- host	base_script	pages
-- www.googletagmanager.com	js	68.23
-- www.googletagmanager.com	gtm.js	40.24
-- connect.facebook.net	fbevents.js	23.78
-- securepubads.g.doubleclick.net	gpt.js	15.11
-- pagead2.googlesyndication.com	ufs_web_display.js	12.29
-- scripts.clarity.ms	clarity.js	12.28
-- www.googletagmanager.com	destination	11.62
-- pagead2.googlesyndication.com	adsbygoogle.js	11.44
-- bat.bing.com	bat.js	9.56
-- www.gstatic.com	recaptcha__en.js	6.59

