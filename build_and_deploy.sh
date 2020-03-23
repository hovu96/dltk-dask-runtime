#!/bin/bash
set -e
set -x

# scheduler
docker build --rm -f "./scheduler/thin.Dockerfile" -t hovu96/dltk-dask-runtime:scheduler-thin .
docker push hovu96/dltk-dask-runtime:scheduler-thin
docker build --rm -f "./scheduler/fat.Dockerfile" -t hovu96/dltk-dask-runtime:scheduler-fat .
docker push hovu96/dltk-dask-runtime:scheduler-fat

# worker
docker build --rm -f "./worker/thin.Dockerfile" -t hovu96/dltk-dask-runtime:worker-thin .
docker push hovu96/dltk-dask-runtime:worker-thin
docker build --rm -f "./worker/fat.Dockerfile" -t hovu96/dltk-dask-runtime:worker-fat .
docker push hovu96/dltk-dask-runtime:worker-fat

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