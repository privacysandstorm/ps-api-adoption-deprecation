#!/bin/sh

outputDataDir=./data/rws
outputDirSuffix=preloaded
mkdir -p ${outputDataDir}/${outputDirSuffix}
cd $outputDataDir

echo "" > primary.txt

## for each commit
while read commit; do
  ##download RWS
  wget "https://raw.githubusercontent.com/GoogleChrome/related-website-sets/$commit/related_website_sets.JSON" -O $outputDirSuffix/$commit.json

  ## extract primary (we just want total unique)
  jq -r '.sets.[].primary' $outputDirSuffix/$commit.json >> primary.txt

done < rws-commits-sha.txt

while read commit; do
  ##download FPS
  wget "https://raw.githubusercontent.com/GoogleChrome/related-website-sets/$commit/first_party_sets.JSON" -O $outputDirSuffix/$commit.json

  ## extract primary (we just want total unique)
  jq -r '.sets.[].primary' $outputDirSuffix/$commit.json >> primary.txt

done < fps-commits-sha.txt

# keep unique primary (corresponds to number of sets)
sort -u primary.txt > unique-primary.txt