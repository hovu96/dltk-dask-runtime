import logging
import json
import subprocess
import sys
import threading
import os
import shutil
from flask import Flask, request, jsonify, Response
import http
import pathlib
from waitress import serve

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

lock = threading.Lock()
algorithm_process = None

models_path = "/models"
code_dir = "/code"
code_module_path = os.path.join(code_dir, "dltk_code.py")
code_version_path = os.path.join(code_dir, "dltk_code.version")

pathlib.Path(code_dir).mkdir(parents=True, exist_ok=True)


def restart_algorithm():
    lock.acquire()
    try:
        global algorithm_process
        if algorithm_process:
            logging.info("terminating current algorithm")
            algorithm_process.terminate()
        logging.info("starting algorithm ...")
        algorithm_process = subprocess.Popen([sys.executable, 'algorithm.py'])
        logging.info("algorithm started")
        return {}
    finally:
        lock.release()


@app.route('/code', methods=['GET', 'PUT'])
def program():
    if request.method == 'PUT':
        logging.info("received new algorithm code")
        version = request.headers['X-Code-Version']
        code = request.data.decode()
        with open(code_module_path, "w") as f:
            f.write(code)
        with open(code_version_path, "w") as f:
            f.write(version)
        a = restart_algorithm()
        return json.dumps(a)
    if request.method == 'GET':
        try:
            with open(code_module_path, 'r') as f:
                code = f.read()
        except FileNotFoundError:
            code = None
        try:
            with open(code_version_path, 'r') as f:
                version = f.read()
        except FileNotFoundError:
            version = 0
        if code is None:
            return '', http.HTTPStatus.NOT_FOUND
        response = Response(code)
        response.headers['X-Code-Version'] = "%s" % version
        return response


@app.route('/models', methods=['GET'])
def list_models():
    model_names = []
    for model_name in os.listdir(models_path):
        if model_name == "lost+found":
            continue
        full_path = os.path.join(models_path, model_name)
        if os.path.isdir(full_path):
            model_names.append(model_name)
    return jsonify(model_names)


@app.route('/model/<model_name>', methods=['PUT', 'DELETE'])
def model(model_name):
    if request.method == 'PUT':
        logging.info("creating model %s ..." % model_name)
        full_path = os.path.join(models_path, model_name)
        os.mkdir(full_path)
        return jsonify({})
    if request.method == 'DELETE':
        logging.info("removing model %s ..." % model_name)
        full_path = os.path.join(models_path, model_name)
        shutil.rmtree(full_path)
        return jsonify({})


if __name__ == '__main__':
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"),
        format='%(asctime)s %(levelname)-8s %(message)s',
    )
    serve(app, host="0.0.0.0", port=5001)
