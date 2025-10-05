# tests/conftest.py
import os, sys, pathlib, pytest

# --- import app for client fixture ---
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from app import create_app
    APP_FACTORY = True
except Exception:
    from app import app as _app  # type: ignore
    APP_FACTORY = False

@pytest.fixture(scope="session")
def app():
    """Create the Flask app in TESTING mode without touching DB."""
    app = create_app() if APP_FACTORY else _app
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=True,
        SERVER_NAME="localhost",
    )
    return app

@pytest.fixture()
def client(app):
    """Standard Flask test client fixture."""
    return app.test_client()
