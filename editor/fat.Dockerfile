FROM hovu96/dltk-dask-runtime:editor-thin
COPY fat-requirements.txt /
RUN pip install --no-cache-dir -r /fat-requirements.txt