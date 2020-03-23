FROM hovu96/dltk-dask-runtime:scheduler-thin
COPY fat-conda-forge-requirements.txt /
RUN conda install -y -c conda-forge --file /fat-conda-forge-requirements.txt
