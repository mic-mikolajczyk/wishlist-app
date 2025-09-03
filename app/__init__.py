from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from config import Config

# Initialize extensions

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # Import models so Flask-Migrate can detect them
    from app.models import models  # noqa: F401

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.frontend import frontend_bp
    from app.routes.public import public_bp
    from app.routes.wishlist import wishlist_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(frontend_bp)

    return app
