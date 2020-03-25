from distributed import Client
import sys
import logging
import os
import datetime
from waitress import serve
from flask import Flask, jsonify, request
app = Flask(__name__)

sys.path.insert(0, "/code")

scheduler_host = os.environ.get("SCHEDULER_HOST")
client = Client(scheduler_host)


@app.route('/fit', methods=['POST'])
def fit():
    logging.info("fitting ...")
    events = request.get_json()

    dltk_code = __import__("dltk_code")

    def fit_impl(events):
        return events
    if hasattr(dltk_code, "fit"):
        fit_impl = getattr(dltk_code, "fit")

    result = fit_impl(events)

    logging.info("fit done")
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
