
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    # Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Simple per-IP rate limit (no MFA allowed in constraints)
    limiter = Limiter(get_remote_address, storage_uri="memory://")
    limiter.init_app(app)

    # Blueprints / routes
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    login_manager.login_view = "main.login"
    return app
