# wsgi.py
import atexit
import logging
import os
import signal
import subprocess
import sys

from dotenv import load_dotenv

load_dotenv()

# 'app' is the WSGI callable that Gunicorn looks for.
from vlab import create_app

app = create_app()

logger = logging.getLogger(__name__)


def _start_tailwind_watch():
    """Launch ``npm run watchCss`` as a background subprocess.

    Returns the ``Popen`` handle or ``None`` if it could not be started.
    Any failure is logged as a warning — the Flask app is never aborted.
    """
    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        proc = subprocess.Popen(
            [npm_cmd, "run", "watchCss"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        logger.info("Tailwind watch process started (pid=%d).", proc.pid)
        return proc
    except FileNotFoundError:
        logger.warning(
            "Could not find '%s' on PATH — Tailwind CSS will not rebuild "
            "automatically. Run 'npm run watchCss' manually or install "
            "Node.js.",
            npm_cmd,
        )
    except OSError as exc:
        logger.warning("Failed to start Tailwind watch process: %s", exc)
    return None


def _cleanup_tailwind(proc):
    """Terminate the Tailwind subprocess gracefully, then force-kill if needed."""
    if proc is None or proc.poll() is not None:
        return  # already dead / never started

    logger.info("Shutting down Tailwind watch (pid=%d)...", proc.pid)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        logger.warning(
            "Tailwind watch (pid=%d) did not exit in time — force-killing.",
            proc.pid,
        )
        proc.kill()
        proc.wait()


if __name__ == "__main__":
    if app.config["ENV"] == "dev":
        tailwind_proc = _start_tailwind_watch()

        if tailwind_proc is not None:
            atexit.register(_cleanup_tailwind, tailwind_proc)

            # Also handle SIGTERM/SIGINT so Ctrl-C kills the subprocess
            def _sig_handler(signum, _frame):
                _cleanup_tailwind(tailwind_proc)
                sys.exit(0)

            signal.signal(signal.SIGTERM, _sig_handler)
            signal.signal(signal.SIGINT, _sig_handler)

        app.run(host="0.0.0.0", port=8000)
