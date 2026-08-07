"""
Database layer for VLab.

Two back-ends, each configured from a single URI string:

* **MySQL** (SQLAlchemy) — primary relational store (users, challenges, state).
* **MongoDB** (PyMongo) — analytics, logs, and unstructured experiment data.

Connections are lazy: nothing touches the network until ``init_db(app)`` is
called from the application factory.
"""

from __future__ import annotations

import logging
from typing import Generator, Optional

from flask import current_app, g

# ---------------------------------------------------------------------------
# SQLAlchemy (MySQL)
# ---------------------------------------------------------------------------
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta, declarative_base

# ---------------------------------------------------------------------------
# PyMongo
# ---------------------------------------------------------------------------
from pymongo import MongoClient
from pymongo.database import Database as MongoDatabase

logger = logging.getLogger(__name__)

# -- module-level singletons (populated by init_db) --------------------------

_engine: Optional[Engine] = None
_Session: Optional[scoped_session] = None
Base: DeclarativeMeta = declarative_base()  # ORM model base

_mongo_client: Optional[MongoClient] = None
_mongo_db: Optional[MongoDatabase] = None


# ===========================================================================
# Public helpers
# ===========================================================================


def init_db(app) -> None:
    """Wire databases into the Flask application.

    Called once from the app factory.  Reads ``DATABASE_URI`` and
    ``MONGODB_URI`` from ``app.config``.
    """
    _init_sqlalchemy(app)
    _init_mongodb(app)

    # Clean up scoped sessions at the end of every request context.
    app.teardown_appcontext(_close_sqlalchemy_session)


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy ``Session`` bound to the current application context.

    Usage (Flask route / view)::

        db = next(get_db())
        user = db.query(User).first()
    """
    if _Session is None:
        raise RuntimeError("Database not initialised — call init_db(app) first.")
    session = _Session()
    try:
        yield session
    finally:
        session.close()


def get_mongo() -> MongoDatabase:
    """Return the MongoDB database handle for the default database."""
    if _mongo_db is None:
        raise RuntimeError("MongoDB not initialised — call init_db(app) first.")
    return _mongo_db


# ===========================================================================
# Internal
# ===========================================================================


def _init_sqlalchemy(app) -> None:
    global _engine, _Session

    uri = app.config.get("DATABASE_URI")
    if not uri:
        logger.warning("DATABASE_URI not set — SQLAlchemy is disabled.")
        return

    _engine = create_engine(
        uri,
        pool_pre_ping=True,  # detect stale connections
        pool_recycle=3600,  # recycle hourly (safe under MySQL wait_timeout)
        echo=app.config.get("DEBUG", False),
    )
    _Session = scoped_session(
        sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    )
    app.extensions["sqlalchemy_engine"] = _engine

    logger.info("SQLAlchemy engine created for %s", repr(uri))


def _init_mongodb(app) -> None:
    global _mongo_client, _mongo_db

    uri = app.config.get("MONGODB_URI")
    if not uri:
        logger.warning("MONGODB_URI not set — MongoDB is disabled.")
        return

    _mongo_client = MongoClient(
        uri,
        tz_aware=True,
        serverSelectionTimeoutMS=5000,
    )
    # Use the database name from the URI; default to "vlab".
    db_name = _mongo_client.get_default_database().name or "vlab"
    _mongo_db = _mongo_client[db_name]

    app.extensions["mongo_client"] = _mongo_client

    logger.info("MongoDB client created (%s / %s)", repr(uri), db_name)


def _close_sqlalchemy_session(_error=None) -> None:
    """Remove the scoped session at the end of the request."""
    if _Session is not None:
        _Session.remove()


# ===========================================================================
# Graceful shutdown (optional — call from a shutdown handler)
# ===========================================================================


def dispose_connections() -> None:
    """Close all connection pools.  Safe to call on process shutdown."""
    if _engine is not None:
        _engine.dispose()
        logger.info("SQLAlchemy engine disposed.")
    if _mongo_client is not None:
        _mongo_client.close()
        logger.info("MongoDB client closed.")
