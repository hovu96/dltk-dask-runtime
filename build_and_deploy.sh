#!/bin/bash
set -e
set -x
docker build --rm -f "./client/Dockerfile" -t hovu96/dltk-dask-runtime:client ./client
docker push hovu96/dltk-dask-runtime:client
docker build --rm -f "./editor/Dockerfile" -t hovu96/dltk-dask-runtime:editor ./editor
docker push hovu96/dltk-dask-runtime:editor