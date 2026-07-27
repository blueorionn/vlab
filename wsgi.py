# wsgi.py
from dotenv import load_dotenv

load_dotenv()

# 'app' is the WSGI callable that Gunicorn looks for.
from vlab import create_app

app = create_app()


if __name__ == "__main__":
    if app.config["ENV"] == "dev":
        app.run(host="0.0.0.0", port=8000)