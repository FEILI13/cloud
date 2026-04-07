#!/bin/bash
set -e

docker build -t ageoverflow .
docker run --rm -p 8080:8080 ageoverflow