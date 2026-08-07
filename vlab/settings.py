"""Application Configuration."""

import os


class Config:
    """Base Configuration."""

    ENV = "dev"
    DEBUG = True
    CORS_ORIGINS = "*"

    SECRET_KEY = os.environ["SECRET_KEY"]
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    MAX_CONTENT_LENGTH = 24 * 1024 * 1024  # 24 megabytes (file size restriction)

    # -- Databases --
    # Single-URI strings so the database layer owns parsing.
    DATABASE_URI = os.getenv(
        "DATABASE_URI",
        "postgresql+psycopg2://vlab:vlab@localhost:5432/vlab",
    )
    MONGODB_URI = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017/vlab",
    )


config = Config()
