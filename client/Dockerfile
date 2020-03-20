FROM python:3.7
ENV APP_DIR /app
WORKDIR ${APP_DIR}
COPY requirements.txt ${APP_DIR}
#RUN apt-get update && apt-get install -y netbase
RUN pip install -r ${APP_DIR}/requirements.txt
COPY *.py ${APP_DIR}/
EXPOSE 5001 5002
ENTRYPOINT ["python", "./manager.py"]
