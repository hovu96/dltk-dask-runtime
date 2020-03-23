FROM daskdev/dask
RUN pip install --no-cache-dir \
    jupyterlab_server
ENV INSTALL_PATH /src
ENV NOTEBOOK_PATH /notebooks
RUN mkdir -p $INSTALL_PATH
WORKDIR $INSTALL_PATH
COPY editor/*.py ./
EXPOSE 8888
WORKDIR $NOTEBOOK_PATH
ENTRYPOINT python $INSTALL_PATH/main.py
