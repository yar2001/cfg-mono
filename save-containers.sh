#!/bin/bash
images=$(docker compose ps --format json | jq -r '.[].Image')

rm -r ./saved

for image in $images
do
  docker save $image | gzip > ./saved/$image.tar.gz
done
