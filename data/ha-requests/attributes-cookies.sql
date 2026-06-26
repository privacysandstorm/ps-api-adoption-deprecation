-- repartition of attributes for cookies

SELECT
  date,
  firstParty,
  SUM(IF(httpOnly = 'true', 1, 0)) / COUNT(0) AS httpOnly,
  SUM(IF(secure = 'true', 1, 0)) / COUNT(0) AS secure,
  SUM(IF(session = 'true', 1, 0)) / COUNT(0) AS session,
  SUM(IF(sameParty = 'true', 1, 0)) / COUNT(0) AS sameParty,
  SUM(IF(sameSite = 'Lax', 1, 0)) / COUNT(0) AS sameSiteLax,
  SUM(IF(sameSite = 'None', 1, 0)) / COUNT(0) AS sameSiteNone,
  SUM(IF(sameSite = 'Strict', 1, 0)) / COUNT(0) AS sameSiteStrict,
  SUM(IF(sameSite IS NULL, 1, 0)) / COUNT(0) AS sameSiteNull,
  SUM(IF(partitionKey IS NOT NULL, 1, 0)) / COUNT(0) AS partitionKey,
  SUM(IF(partitionKeyOpaque IS NOT NULL, 1, 0)) / COUNT(0) AS partitionKeyOpaque,
  SUM(IF(STARTS_WITH(name, '__Host-'), 1, 0)) / COUNT(0) AS hostPrefix,
  SUM(IF(STARTS_WITH(name, '__Secure-'), 1, 0)) / COUNT(0) AS securePrefix
FROM `gcp-anonymized-project-name.privacysandbox.cookies-custom-metrics`
WHERE
  firstParty IS NOT NULL -- just in case
GROUP BY
  date, firstParty

