# app/__init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def _resolve_database_uri(app: Flask) -> str:
    """
    Priority:
      1) DATABASE_URL env (Render Postgres or custom URI)
      2) SQLITE_DIR env (e.g., persistent disk mount like /var/data), mats.db inside it
      3) app.instance_path/mats.db
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url

    base_dir = os.getenv("SQLITE_DIR", app.instance_path)
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, "mats.db")
    return f"sqlite:///{path}?check_same_thread=false"

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object("config.Config")

    os.makedirs(app.instance_path, exist_ok=True)


    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", os.urandom(32)))

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", _resolve_database_uri(app))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {"pool_pre_ping": True})

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    limiter = Limiter(
        key_func=get_remote_address,
        storage_uri=os.getenv("RATE_LIMIT_STORAGE", "memory://"),
        default_limits=[os.getenv("DEFAULT_RATE_LIMIT", "200/hour")],
    )
    limiter.init_app(app)

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    login_manager.login_view = "main.login"

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}, 200

    return app
