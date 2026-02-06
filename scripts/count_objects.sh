#!/bin/bash

AWS_PROFILE="staging-piksel"
BUCKET="piksel-staging-public-data"
PREFIX="gm_s2/0.0.1/"

suffixes=("sha1" "stac-item.json" "BCMAD.tif" "COUNT.tif" "EMAD.tif" "SMAD.tif" "blue.tif" "green.tif" "nir.tif" "red.tif" "rgba.tif" "swir16.tif" "swir22.tif")

aws s3 ls s3://${BUCKET}/${PREFIX} --recursive --profile ${AWS_PROFILE} | awk -v suffixes="${suffixes[*]}" '
BEGIN {
    split(suffixes, arr, " ")
    for (i in arr) counts[arr[i]] = 0
}
{
    for (suffix in counts) {
        if ($NF ~ suffix "$") counts[suffix]++
    }
}
END {
    for (suffix in counts) print suffix ": " counts[suffix]
}
'
