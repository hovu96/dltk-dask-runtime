import logging
import json
import subprocess
import sys
import threading
import traceback
import os
import shutil
from flask import Flask, request, jsonify, Response
import http
import pathlib
import time
import signal
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


class WaitForAlgorithm(threading.Thread):
    def __init__(self, process):
        threading.Thread.__init__(self)
        self.process = process
        self.daemon = True
        self.start()

    def run(self):
        try:
            while True:
                try:
                    code = self.process.wait(timeout=0.2)
                    logging.info("algorithm subprocess existed with code %s" % code)
                    if code == 15:  # SIGTERM
                        pass
                    elif code == 9:  # SIGKILL
                        pass
                    elif code == -9:
                        logging.warning("algorithm ran out of memory")
                        restart_algorithm()
                    break
                except subprocess.TimeoutExpired:
                    time.sleep(10)
        except:
            msg = traceback.format_exc()
            logging.error("unexpected error in wait for algo thread: %s" % msg)


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
        WaitForAlgorithm(algorithm_process)
        return {}
    finally:
        lock.release()


@app.route('/algo_status', methods=['GET'])
def algo_status():
    poll_result = algorithm_process.poll()
    return Response("%s" % {
        "poll_result": poll_result,
        "returncode": algorithm_process.returncode,
        "pid": algorithm_process.pid,
    })


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
