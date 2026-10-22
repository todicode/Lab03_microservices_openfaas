"""Local/container HTTP adapter. Production functions use the official OpenFaaS template."""
import importlib
import logging
import os
from types import SimpleNamespace

from flask import Flask, jsonify, request
from waitress import serve

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 65_536
module = importlib.import_module("services." + os.environ["SERVICE_MODULE"])


@app.errorhandler(413)
def too_large(exc):
    return jsonify(error={"code": "payload_too_large", "message": "Nội dung vượt quá 64 KiB."}), 413


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def dispatch(path):
    event = SimpleNamespace(path=request.path, method=request.method, headers=dict(request.headers),
                            query=request.args, body=request.get_data())
    res = module.handle(event, SimpleNamespace(hostname=os.getenv("HOSTNAME", "localhost")))
    return jsonify(res["body"]), res["statusCode"], res["headers"]


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=int(os.getenv("PORT", "8080")), threads=8)

