from distributed import Client
import sys
import logging
import os
import datetime
import traceback
from waitress import serve
from flask import Flask, jsonify, request
app = Flask(__name__)

sys.path.insert(0, "/code")

scheduler_host = os.environ.get("SCHEDULER_HOST")
client = Client(scheduler_host)


@app.route('/execute/<method>', methods=['POST'])
def execute(method):
    logging.info("executing ...")
    events = request.get_json()

    try:
        dltk_code = __import__("dltk_code")
    except:
        return "Error importing algo:\n%s" % traceback.format_exc(), 500

    if not hasattr(dltk_code, method):
        return "Method '%s' not found:\n%s" % method, 400
    method_impl = getattr(dltk_code, method)

    try:
        result = method_impl(events)
    except:
        return "Error calling algo method:\n%s" % traceback.format_exc(), 500
        # return "Error calling algo method", 500

    logging.info("execute finished")
    return jsonify(result)


if __name__ == '__main__':
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"),
        format='%(asctime)s %(levelname)-8s %(message)s',
    )
    serve(
        app,
        host="0.0.0.0",
        port=5002,
        channel_timeout=100000,
    )
