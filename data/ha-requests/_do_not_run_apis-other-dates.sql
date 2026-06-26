-- regex for api methods and headers
-- dates to adjust either one by one or use an IN ('', '') statement
-- about 300GB per crawl for more recent dates (varies by date)
-- note: you probably do not want to run this query as it is pretty expensive
-- this does not save response_body on purpose (we only kept it for 2024-09-01 when adoption peaked and started to stagnate)
-- otherwise too expensive to save and keep the response_body (see `apis-2024-09-01.sql`)
--


CREATE TEMPORARY FUNCTION parse_privacy_sandbox_apis(response_body STRING)
RETURNS STRUCT<
  attribution BOOL,
  fedcm BOOL,
  fenced_frames BOOL,
  floc BOOL,
  private_aggregation BOOL,
  private_state_tokens BOOL,
  protected_audience BOOL,
  shared_storage BOOL,
  storage_access BOOL,
  topics BOOL,
  ua_client_hints BOOL,
  total_apis INTEGER
>
LANGUAGE js AS """
  if (!response_body) {
    return {
      attribution: false,
      fedcm: false,
      fenced_frames: false,
      floc: false,
      private_aggregation: false,
      private_state_tokens: false,
      protected_audience: false,
      shared_storage: false,
      storage_access: false,
      topics: false,
      ua_client_hints: false,
      total_apis: 0
    };
  }

  const body = response_body.toLowerCase();

  const attribution = /.setattributionreporting|attributionsrc|attribution-reporting-eligible|attribution-reporting-register-source|attribution-reporting-register-trigger/.test(body);

  const fedcm = /.credentials.get|identitycredential.disconnect|identityprovider.close|identityprovider.getuserinfo|.login.setstatus/.test(body);
  //ignore set-login (FP risk))

  const fenced_frames = /fencedframe|fenced-frame|.getnestedconfigs|.reportevent|.setsharedstoragecontext|.setreporteventdataforautomationbeacons/.test(body);

  const floc = /.interestcohort/.test(body);

  const private_aggregation = /.contributetohistogram|.enabledebugmode/.test(body);

  const private_state_tokens = /.hasprivatetoken|.hasredemptionrecord|.setprivatetoken|sec-private-state-token|sec-redemption-record/.test(body);

  const protected_audience = /.joinadinterestgroup|.leaveadinterestgroup|.clearoriginjoinedadinterestgroups|.runadauction|.adauctioncomponents|.createauctionnonce|ad-auction-allowed|ad-auction-only|ad-auction-signals|ad-auction-additional-bid|x-fledge-bidding-signals-format-version|sec-ad-auction-fetch/.test(body);
  //ignore data-version (FP risk)

  const shared_storage = /.sharedstorage|sec-shared-storage-writable|sec-shared-storage-data-origin|shared-storage-write|shared-storage-cross-origin-worklet-allowed/.test(body);

  const storage_access = /.requeststorageaccess|.hasstorageaccess|.hasunpartitionedcookieaccess|sec-fetch-storage-access|activate-storage-access/.test(body);

  const topics = /.browsingtopics|sec-browsing-topics|observe-browsing-topics/.test(body);

  const ua_client_hints = /.useragentdata.tojson|.gethighentropyvalues|accept-ch|critical-ch|delegate-ch|sec-ch-ua/.test(body);

  return {
      attribution: attribution,
      fedcm: fedcm,
      fenced_frames: fenced_frames,
      floc: floc,
      private_aggregation: private_aggregation,
      private_state_tokens: private_state_tokens,
      protected_audience: protected_audience,
      shared_storage: shared_storage,
      storage_access: storage_access,
      topics: topics,
      ua_client_hints: ua_client_hints,
      total_apis: (attribution ? 1 : 0) + (fedcm ? 1 : 0) + (fenced_frames ? 1 : 0) + (floc ? 1 : 0) + (private_aggregation ? 1 : 0) + (private_state_tokens ? 1 : 0) + (protected_audience ? 1 : 0) + (shared_storage ? 1 : 0) + (storage_access ? 1 : 0) + (topics ? 1 : 0) + (ua_client_hints ? 1 : 0)
  };
""";

INSERT INTO `gcp-anonymized-project-name.privacysandbox.apis` (
  date,
  page,
  rank,
  url,
  host,
  is_main_document,
  type,
  script_name,
  attribution,
  fedcm,
  fenced_frames,
  floc,
  private_aggregation,
  private_state_tokens,
  protected_audience,
  shared_storage,
  storage_access,
  topics,
  ua_client_hints,
  total_apis
)

WITH kfeatures AS (
  SELECT
    date,
    page,
    rank
  FROM
    `gcp-anonymized-project-name.privacysandbox.kfeatures-pages`
  WHERE
    date = '2021-03-01' AND
    -- date = '2021-04-01' AND
    -- date = '2021-05-01' AND
    -- date = '2021-06-01' AND
    -- date = '2021-07-01' AND
    -- date = '2021-08-01' AND
    -- date = '2021-09-01' AND
    -- date = '2021-10-01' AND
    -- date = '2021-11-01' AND
    -- date = '2021-12-01' AND
    -- date = '2022-01-01' AND
    -- date = '2022-02-01' AND
    -- date = '2022-03-01' AND
    -- date = '2022-04-01' AND
    -- date = '2022-05-01' AND
    -- date = '2022-06-01' AND
    -- date = '2022-07-01' AND
    -- date = '2022-08-01' AND
    -- date = '2022-09-01' AND
    -- date = '2022-10-01' AND
    -- date = '2022-11-01' AND
    -- date = '2022-12-01' AND
    -- date = '2023-01-01' AND
    -- date = '2023-02-01' AND
    -- date = '2023-03-01' AND
    -- date = '2023-04-01' AND
    -- date = '2023-05-01' AND
    -- date = '2023-06-01' AND
    -- date = '2023-07-01' AND
    -- date = '2023-08-01' AND
    -- date = '2023-09-01' AND
    -- date = '2023-10-01' AND
    -- date = '2023-11-01' AND
    -- date = '2023-12-01' AND
    -- date = '2024-01-01' AND
    -- date = '2024-02-01' AND
    -- date = '2024-03-01' AND
    -- date = '2024-04-01' AND
    -- date = '2024-05-01' AND
    -- date = '2024-06-01' AND
    -- date = '2024-07-01' AND
    -- date = '2024-08-01' AND
    -- date = '2024-10-01' AND
    -- date = '2024-11-01' AND
    -- date = '2024-12-01' AND
    -- date = '2025-01-01' AND
    -- date = '2025-02-01' AND
    -- date = '2025-03-01' AND
    -- date = '2025-04-01' AND
    -- date = '2025-05-01' AND
    -- date = '2025-06-01' AND
    -- date = '2025-07-01' AND
    -- date = '2025-08-01' AND
    -- date = '2025-09-01' AND
    -- date = '2025-10-01' AND
    -- date = '2025-11-01' AND
    -- date = '2025-12-01' AND
    -- date = '2026-01-01' AND
    -- date = '2026-02-01' AND
    -- date = '2026-03-01' AND
    -- date = '2026-04-01' AND
    client = 'desktop' AND
    is_root_page
)

SELECT
  date,
  page,
  rank,
  url,
  NET.HOST(url) AS host,
  is_main_document,
  type,
  script_name,
  result.attribution,
  result.fedcm,
  result.fenced_frames,
  result.floc,
  result.private_aggregation,
  result.private_state_tokens,
  result.protected_audience,
  result.shared_storage,
  result.storage_access,
  result.topics,
  result.ua_client_hints,
  result.total_apis
FROM (
  SELECT
    requests.date,
    requests.page,
    requests.rank,
    requests.url,
    requests.is_main_document,
    requests.type,
    REGEXP_EXTRACT(requests.url, r'([^/]+)$') AS script_name,
    parse_privacy_sandbox_apis(requests.response_body) AS result,
    requests.response_body
  FROM `httparchive.crawl.requests` AS requests
  WHERE
    requests.date = '2021-03-01' AND
    -- requests.date = '2021-04-01' AND
    -- requests.date = '2021-05-01' AND
    -- requests.date = '2021-06-01' AND
    -- requests.date = '2021-07-01' AND
    -- requests.date = '2021-08-01' AND
    -- requests.date = '2021-09-01' AND
    -- requests.date = '2021-10-01' AND
    -- requests.date = '2021-11-01' AND
    -- requests.date = '2021-12-01' AND
    -- requests.date = '2022-01-01' AND
    -- requests.date = '2022-02-01' AND
    -- requests.date = '2022-03-01' AND
    -- requests.date = '2022-04-01' AND
    -- requests.date = '2022-05-01' AND
    -- requests.date = '2022-06-01' AND
    -- requests.date = '2022-07-01' AND
    -- requests.date = '2022-08-01' AND
    -- requests.date = '2022-09-01' AND
    -- requests.date = '2022-10-01' AND
    -- requests.date = '2022-11-01' AND
    -- requests.date = '2022-12-01' AND
    -- requests.date = '2023-01-01' AND
    -- requests.date = '2023-02-01' AND
    -- requests.date = '2023-03-01' AND
    -- requests.date = '2023-04-01' AND
    -- requests.date = '2023-05-01' AND
    -- requests.date = '2023-06-01' AND
    -- requests.date = '2023-07-01' AND
    -- requests.date = '2023-08-01' AND
    -- requests.date = '2023-09-01' AND
    -- requests.date = '2023-10-01' AND
    -- requests.date = '2023-11-01' AND
    -- requests.date = '2023-12-01' AND
    -- requests.date = '2024-01-01' AND
    -- requests.date = '2024-02-01' AND
    -- requests.date = '2024-03-01' AND
    -- requests.date = '2024-04-01' AND
    -- requests.date = '2024-05-01' AND
    -- requests.date = '2024-06-01' AND
    -- requests.date = '2024-07-01' AND
    -- requests.date = '2024-08-01' AND
    -- requests.date = '2024-10-01' AND
    -- requests.date = '2024-11-01' AND
    -- requests.date = '2024-12-01' AND
    -- requests.date = '2025-01-01' AND
    -- requests.date = '2025-02-01' AND
    -- requests.date = '2025-03-01' AND
    -- requests.date = '2025-04-01' AND
    -- requests.date = '2025-05-01' AND
    -- requests.date = '2025-06-01' AND
    -- requests.date = '2025-07-01' AND
    -- requests.date = '2025-08-01' AND
    -- requests.date = '2025-09-01' AND
    -- requests.date = '2025-10-01' AND
    -- requests.date = '2025-11-01' AND
    -- requests.date = '2025-12-01' AND
    -- requests.date = '2026-01-01' AND
    -- requests.date = '2026-02-01' AND
    -- requests.date = '2026-03-01' AND
    -- requests.date = '2026-04-01' AND
    requests.client = 'desktop' AND
    requests.is_root_page AND
    requests.rank <= 100000 AND
    ( requests.type = 'script' OR requests.type = 'html' ) AND
    EXISTS (
      SELECT 1
      FROM kfeatures AS filter
      WHERE filter.date = requests.date AND
        filter.page = requests.page
      ) AND
    requests.response_body IS NOT NULL
)
WHERE
  result.total_apis > 0
