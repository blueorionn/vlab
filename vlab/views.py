"""Base views."""

import os
from flask import current_app, Blueprint, send_file

blueprint = Blueprint("base", __name__)


@blueprint.route("/robots.txt")
def server_robots():
    path = os.path.join(current_app.config["APP_DIR"], "static/public/robots.txt")

    return send_file(path, mimetype="text/plain")


@blueprint.route("/favicon.ico")
def serve_favicon():
    path = os.path.join(current_app.config["APP_DIR"], "static/public/favicon.ico")

    return send_file(path, mimetype="image/x-icon")
