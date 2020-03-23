#!/bin/bash
set -e
set -x

# client
docker build --rm -f "./client/thin.Dockerfile" -t hovu96/dltk-dask-runtime:client-thin .
docker push hovu96/dltk-dask-runtime:client-thin
docker build --rm -f "./client/fat.Dockerfile" -t hovu96/dltk-dask-runtime:client-fat .
docker push hovu96/dltk-dask-runtime:client-fat

# editor
docker build --rm -f "./editor/thin.Dockerfile" -t hovu96/dltk-dask-runtime:editor-thin .
docker push hovu96/dltk-dask-runtime:editor-thin
docker build --rm -f "./editor/fat.Dockerfile" -t hovu96/dltk-dask-runtime:editor-fat .
docker push hovu96/dltk-dask-runtime:editor-fat