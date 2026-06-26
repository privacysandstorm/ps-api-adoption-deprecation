#!/bin/sh

outputDataDir=./data/attestations
outputDirSuffix=preloaded
mkdir -p ${outputDataDir}/${outputDirSuffix}
cd $outputDataDir

## extract commits into commits.txt
jq -r '.payload.commitGroups.[].commits.[].oid' github-payload.json > commits.txt

## for each commit
while read commit; do
  ## download the manifest
  wget -q "https://raw.githubusercontent.com/chromium/chromium/$commit/components/privacy_sandbox/privacy_sandbox_attestations/preload/manifest.json" -O manifest.json
  ##get the version
  VERSION="$(jq -r '.version' manifest.json)"
  echo "New version - $VERSION"
  ##download the list of authorized callers, and rename
  wget -q "https://raw.githubusercontent.com/chromium/chromium/$commit/components/privacy_sandbox/privacy_sandbox_attestations/preload/privacy-sandbox-attestations.dat" -O $outputDirSuffix/$VERSION.dat
  rm manifest.json
done < commits.txt

rm commits.txt

## Download the proto file to parse authorized callers
wget -q "https://raw.githubusercontent.com/chromium/chromium/refs/heads/main/components/privacy_sandbox/privacy_sandbox_attestations/proto/privacy_sandbox_attestations.proto" -O privacy_sandbox_attestations.proto
protoc "privacy_sandbox_attestations.proto" --proto_path=. --python_out=.
