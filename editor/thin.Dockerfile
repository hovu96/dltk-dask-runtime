FROM daskdev/dask
RUN pip install --no-cache-dir \
    jupyterlab_server
ENV INSTALL_PATH /src
ENV NOTEBOOK_PATH /notebooks
ENV DLTK_API_DIR /api
RUN mkdir -p $DLTK_API_DIR
RUN mkdir -p $INSTALL_PATH
WORKDIR $INSTALL_PATH
COPY api/ $DLTK_API_DIR/
COPY editor/*.py ./
EXPOSE 8888
WORKDIR $NOTEBOOK_PATH
ENTRYPOINT python $INSTALL_PATH/main.py
