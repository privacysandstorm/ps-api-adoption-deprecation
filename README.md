# Artifact for "Lessons from the Adoption and Deprecation of the Privacy Sandbox Web APIs"

Find more details about our analysis in our paper [Lessons from the Adoption and Deprecation of the Privacy Sandbox Web APIs](https://doi.org/10.48550/arXiv.2606.26390):

```bibtex
@misc{beuginLessonsAdoptionDeprecation2026,
  title = {Lessons from the Adoption and Deprecation of the Privacy Sandbox Web APIs},
  author = {Yohan Beugin and Paul Barford and Patrick McDaniel},
  month = jun,
  year = {2026},
  doi = {10.48550/arXiv.2606.26390},
}
```

Next you will find documentation on how to install dependencies, obtain the data, and reproduce our results.

## Repository Structure
```
apis.json
attestations-preloaded.sh
attestations.py
categories/
--> cloudflare_api.py
--> cloudflare-categories.json
--> cloudflare_categorization.sh
--> set_cloudflare_env.sh.github
data/
--> attestations
--> background-table-start.tex
--> ha-blink
--> ha-pages
--> ha-requests
--> rws
--> telemetry
Dockerfile
figs/
--> appendix-apis-table.tex
--> attestations
--> background-table.tex
--> ha-blink
--> ha-pages
--> ha-requests
--> telemetry
ha-blink.py
ha-pages.py
ha-requests.py
latex-files.py
README.md
requirements.txt
rws-preloaded.sh
telemetry.py
utils.py
```

## [`apis.json`](apis.json)

Details about each API aggregated in a single JSON file.
The majority of the information was collected from the official explainers and developer documentations for each API which we cross-referenced and merged with the following sources:
- Chrome release dates: https://github.com/mdn/browser-compat-data/blob/main/browsers/chrome.json
- Chromium web features list: https://github.com/chromium/chromium/blob/main/third_party/blink/public/mojom/use_counter/metrics/web_feature.mojom
- MDN guides: https://developer.mozilla.org/en-US/docs/Web/Privacy/Guides/Privacy_sandbox
- Permissions policy: https://github.com/w3c/webappsec-permissions-policy/blob/main/features.md#standardized-features
- Permissions policy (bis): https://web.archive.org/web/20250430184208/https://privacysandbox.google.com/private-advertising/setup/web/permissions-policy

Notes:
- RWS can not be called through JS or HTTP Header and does not have any kFeature associated to it.
- `extra` API for kFeature `kPrivacySandboxAdsAPIs` of id 4187 that corresponds to ads APIs (Topics, Protected Audience, Attribution Reporting, etc.) enabled.

## Getting Started

0. Prerequisite: downloading this code repository and having Docker Engine installed.
1. Build the Docker image:
```bash
docker build -t ps-adoption:main .
```
2. Launch the Docker container, attach the current working directory (i.e., run from the root of the code repository) as a volume, set the context to be that volume, and provide an interactive bash terminal:
```bash
docker run --rm -it -v ${PWD}:/workspaces/code \
  -w /workspaces/code \
  --entrypoint bash ps-adoption:main
```
3. Execute the different scripts (see sections below).


## Chrome Status Telemetry

The Chrome team instruments many web features in their browser to monitor their usage over time.
Aggregated statistics can be found on [Chrome platform status's website](https://chromestatus.com/).
For that, we need to know the different "kfeatures" for the Privacy Sandbox that are monitored and instrumented in Chrome.

The entire list of features can be browsed [here](https://github.com/chromium/chromium/blob/main/third_party/blink/public/mojom/use_counter/metrics/web_feature.mojom), refer to [`../apis.json`](../apis.json) for the mapping we extracted between features and Privacy Sandbox APIs.

Usage:
```sh
python3 telemetry.py -type download
python3 telemetry.py -type merge
python3 telemetry.py -type plotAll
python3 telemetry.py -type plotAll --no-logScale
python3 telemetry.py -type plotMax
python3 telemetry.py -type plotMax --no-logScale
python3 telemetry.py -type stats > figs/telemetry/telemetry-stats.txt
```

Output (if default paths not changed):
- Telemetry data in raw format under `./data/telemetry/` and merged `./data/telemetry-merged/`
- Figures and statistics under `./figs/telemetry/`

## HTTP Archive

HTTP Archive dataset can be queried for data related to the adoption of the Privacy Sandbox APIs.
We provide the corresponding SQL queries that we executed along with their data dumps (when not too big) in the respective directories under `./data/`

### Blink features (`/data/ha-blink/`)

HA aggregates into a separate table stats for each blink feature encountered during their crawl, this is also used by chromestatus.com

Usage:
```sh
python3 ha-blink.py -type merge
python3 ha-blink.py -type plotAll
python3 ha-blink.py -type plotAll --no-logScale
python3 ha-blink.py -type plotMax
python3 ha-blink.py -type plotMax --no-logScale
python3 ha-blink.py -type stats > figs/ha-blink/ha-blink-stats.txt
```

Output (if default paths not changed):
- Data merged `./data/ha-blink/merged/`
- Figures and statistics under `./figs/ha-blink/`

### Pages features (`./data/ha-pages/`)

The prior blink features are convenient, but the aggregation step performed by HA removes visibility on the pages these features were detected on.
For finer granularity, next we reparse ourselves the `pages` table of the HA dataset.

Usage:
```sh
python3 ha-pages.py -type merge
python3 ha-pages.py -type plotAll
python3 ha-pages.py -type plotAll --no-logScale
python3 ha-pages.py -type plotMax
python3 ha-pages.py -type plotMax --no-logScale
python3 ha-pages.py -type stats > figs/ha-pages/ha-pages-stats.txt
```

Output (if default paths not changed):
- Data merged `./data/ha-pages/merged/`
- Figures and statistics under `./figs/ha-pages/`


### Requests: HTTP headers, cookies, response bodies (`./data/ha-requests/`)

See the `.sql` queries provided under `/data/ha-requests` to parse the HTTP Archive dataset.
Warning: some of these queries process large amount of data ()

Note: May 2022 crawl does not have `response_body` data due to an issue with HTTP Archive crawl that month (see https://httparchive.org/faq#what-changes-have-been-made-to-the-test-environment-that-might-affect-the-data)

Usage:
```sh
python3 ha-requests.py -plot CHIPS
python3 ha-requests.py -plot adopters
```

## Attestations Dataset

Google required API callers to go through an attestation process to be able to use certain web and Android APIs from the Privacy Sandbox.

A list of authorized callers was then pre-loaded into Chrome and checked regularly for updates. Here is [the corresponding Chromium component](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/privacy_sandbox/privacy_sandbox_attestations/preload) with:
- `privacy-sandbox-attestation.dat` containing the list of authorized callers.
- `manifest.json` indicating the version of the list.

`privacy-sandbox-attestation.dat` can be read with this [proto file](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/privacy_sandbox/privacy_sandbox_attestations/proto/privacy_sandbox_attestations.proto).

Note: info is also accessible through the [GitHub mirror](https://github.com/chromium/chromium/tree/main/components/privacy_sandbox/privacy_sandbox_attestations/preload) of Chromium.

The log of edits to `privacy-sandbox-attestation.dat` is [here](https://chromium.googlesource.com/chromium/src/+log/refs/heads/main/components/privacy_sandbox/privacy_sandbox_attestations/preload/privacy-sandbox-attestations.dat).

Usage:
- [Optional] Obtain the commits for each modification by inspecting the history page of [`privacy-sandbox-attestation.dat`](https://github.com/chromium/chromium/commits/main/components/privacy_sandbox/privacy_sandbox_attestations/preload/privacy-sandbox-attestations.dat), and save the data into `./data/attestations/github-payload.json` (step optional as we already provide the file).

- Download each version of the pre-loaded attestations file into `./data/attestations/pre-loaded` by executing `./attestations-preloaded.sh`

- Now, parse attestations into `./data/attestations/attestations.tsv` by executing `python3 attestations.py -type merge`

- [Optional] Extract unique origins into `./data/attestations/unique-origins.txt` (step optional as we already provide the file).

- [Optional] Classify `unique-origins.txt` with:
  - [Optional] Forcepoint ThreatSeeker URL categorization tool through [this URL](https://support.forcepoint.com/s/site-lookup) and save into `./data/attestations.categories-threatseeker.tsv` (step optional as we already provide the file).
  - [Optional] Cloudflare categorization service by executing `./categories/cloudflare-categorization.sh ./data/attestations/unique-origins.txt ./data/attestations/categories-cloudflare.tsv` **after** completing `set_cloudflare_env.sh.github` with your API keys and renaming the file to `set_cloudflare_env.sh` (step optional as we already provide the file).

- Plot figures under `./figs/attestations` by running `python3 attestations.py -type plot`


## RWS

Edits history parsed similarly to attestation above.
- `git clone https://github.com/GoogleChrome/related-website-sets/commits/main/related_website_sets.JSON`
- `git log --follow --pretty=format:"%H - %ad : %s" --date=short -- related_website_sets.JSON > ../rws-commits.txt` to extract commits (adapt format to get only sha)
- file was renamed from `first_party_sets.JSON` to `related_website_sets.JSON` after commit `677ea7269f18c3c6f769274f7df715e158935682` (before `6582c31453d416722aa230339ba1bcc6efbb2e4e`)
- see `./rws-preloaded.sh` for download and parsing

## LaTex Tables & Paper Appendix

Generate automatically some tables in LaTex for the paper.

Usage: `python3 latex-files.py`
Output:
- `./figs/background-table.tex`
- `./figs/appendix-apis-table.tex`
