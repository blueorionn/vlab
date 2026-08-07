"""Authentication blueprint — signup, login, logout."""

from flask import Blueprint

blueprint = Blueprint("auth", __name__, url_prefix="/auth")

# Import views so routes are registered on the blueprint.
from . import views  # noqa: F401, E402
