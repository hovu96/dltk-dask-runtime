FROM daskdev/dask
RUN pip install --no-cache-dir \
    Flask \
    waitress
ENV APP_DIR /app
WORKDIR ${APP_DIR}
COPY client/*.py ${APP_DIR}/
EXPOSE 5001 5002
ENTRYPOINT ["python", "./manager.py"]