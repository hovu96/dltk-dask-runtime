from distributed import Client
import sys
import logging
import os
import datetime
import traceback
import json
from waitress import serve
from flask import Flask, jsonify, request, Response
from execution_context import Context
import opentracing
from signalfx_tracing import create_tracer
import socket

app = Flask(__name__)
sys.path.insert(0, "/code")


def is_truthy(s):
    return str(s).lower() in ['1', 't', 'true', 'y', 'yes', 'enable', 'enabled']


@app.route('/execute/<method>', methods=['POST'])
def execute(method):
    span_context = opentracing.tracer.extract(
        format=opentracing.propagation.Format.HTTP_HEADERS,
        carrier=dict(request.headers),
    )
    with opentracing.tracer.start_active_span(
        operation_name="method_handler",
        child_of=span_context,
        tags={
            opentracing.ext.tags.SPAN_KIND: opentracing.ext.tags.SPAN_KIND_RPC_SERVER,
            "host": socket.gethostname(),
        }
    ) as scope:
        scope.span.set_tag("method", method)

        response_messages = []
        response_data = None
        algo_error = None
        final_response = True
        try:
            if dltk_code_import_error:
                raise Exception("Error importing algo module: %s" % dltk_code_import_error)
            if not hasattr(dltk_code, method):
                raise Exception("Method '%s' not found:\n%s" % method)

            ctx = Context()
            if "X-Is-Preop" in request.headers:
                ctx.is_preop = is_truthy(request.headers["X-Is-Preop"])
            if "X-Splunk-Server" in request.headers:
                ctx.splunk_server = request.headers["X-Splunk-Server"]
            if "X-SID" in request.headers:
                ctx.sid = request.headers["X-SID"]
            if "X-DLTK-RootContext" in request.headers:
                ctx.root_trace_context_string = request.headers["X-DLTK-RootContext"]

            with opentracing.tracer.start_active_span("parse_data") as scope:
                events = request.get_json()
                scope.span.set_tag("event_count", len(events))

            with opentracing.tracer.start_active_span("call_algo"):
                method_impl = getattr(dltk_code, method)
                response_data, final_response = method_impl(events, ctx)
        except:
            algo_error = traceback.format_exc()
            logging.warning(algo_error)

        with opentracing.tracer.start_active_span("build_response") as scope:
            response_body = {
                "messages": response_messages,
                "final": final_response,
                "error": algo_error,
            }
            if not response_data is None:
                response_body["data"] = response_data
            response = Response(json.dumps(response_body))
            response.status_code = 500 if algo_error else 200
            scope.span.set_tag("error", algo_error)
            scope.span.set_tag("status", response.status_code)
            response.headers['Content-Type'] = "application/json"
            logging.info("finished with status code %s" % response.status_code)
            return response


if __name__ == '__main__':
    logging.basicConfig(
        level=os.environ.get("LOGLEVEL", "INFO"),
        format='%(asctime)s %(levelname)-8s %(message)s',
    )

    logging.info("connecting to scheduler...")
    scheduler_host = os.environ.get("SCHEDULER_HOST")
    client = Client(scheduler_host)

    logging.info("loading algo...")
    dltk_code_import_error = None
    try:
        dltk_code = __import__("dltk_code")
    except:
        dltk_code_import_error = traceback.format_exc()
        logging.info("error loading algo: %s" % dltk_code_import_error)

    tracer_config = {
        "sampler": {
            "type": "const",
            "param": 1,
        },
        "logging": False,
    }

    jaeger_endpoint = None
    signalfx_agent_host = os.getenv('SIGNALFX_AGENT_HOST')
    if signalfx_agent_host:
        jaeger_endpoint = 'http://' + signalfx_agent_host + ':9080/v2/trace'
    endpoint_url_path = "/opentracing/endpoint"
    if os.path.exists(endpoint_url_path):
        with open(endpoint_url_path, 'r') as f:
            jaeger_endpoint = f.read()
    if jaeger_endpoint:
        tracer_config["jaeger_endpoint"] = jaeger_endpoint

    password_path = "/opentracing/password"
    if os.path.exists(password_path):
        with open(password_path, 'r') as f:
            jaeger_password = f.read()
    if jaeger_password:
        tracer_config["jaeger_password"] = jaeger_password

    user_path = "/opentracing/user"
    if os.path.exists(user_path):
        with open(user_path, 'r') as f:
            jaeger_user = f.read()
    if jaeger_user:
        tracer_config["jaeger_user"] = jaeger_user

    tracer = create_tracer(
        config=tracer_config,
        service_name="dltk-dask-client",
        validate=True,
    )

    concurrent_algo_executions = int(os.environ.get("CONCURRENT_ALGO_EXECUTIONS"))
    logging.info("starting server on %s threads..." % concurrent_algo_executions)
    serve(
        app,
        host="0.0.0.0",
        port=5002,
        channel_timeout=100000,
        threads=concurrent_algo_executions,
    )
