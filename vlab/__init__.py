"""Main application package."""

from flask import Flask
from vlab.settings import config

from vlab import core
from .views import blueprint as base_blueprint


def create_app(config_object=config):
    """Create an application factory

    :param config_object: The configuration object to use
    """
    app = Flask(__name__)
    app.config.from_object(config_object)

    # log config_object type
    app.logger.info(f"Using {config_object.__class__.__name__}")
    app.logger.info(f"Debug mode is {config_object.DEBUG}")

    register_blueprints(app)

    return app


def register_blueprints(app: Flask):
    """Registering blueprints."""

    app.register_blueprint(base_blueprint)
    app.register_blueprint(core.views.blueprint)
