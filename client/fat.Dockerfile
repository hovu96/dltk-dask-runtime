FROM hovu96/dltk-dask-runtime:client-thin
COPY fat-requirements.txt /
RUN pip install --no-cache-dir -r /fat-requirements.txt