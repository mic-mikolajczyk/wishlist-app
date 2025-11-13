from flask import Flask
from flask import redirect, request, session, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel

from config import Config

# Initialize extensions

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()
babel = Babel()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    # Locale selection helper

    def select_locale():
        return session.get('lang', app.config.get('BABEL_DEFAULT_LOCALE', 'pl'))

    babel.init_app(app, locale_selector=select_locale)

    # Import models so Flask-Migrate can detect them
    from app.models import models  # noqa: F401

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.frontend import frontend_bp
    from app.routes.public import public_bp
    from app.routes.wishlist import wishlist_bp
    from app.routes.events import events_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(wishlist_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(frontend_bp)

    # Expose locale helper to Jinja (for html lang attr)
    app.jinja_env.globals['get_locale'] = select_locale

    # Simple language switch route (optional UI hook)
    @app.route('/lang/<locale>')
    def set_language(locale):
        if locale in app.config.get('LANGUAGES', []):
            session['lang'] = locale
        return redirect(request.referrer or url_for('frontend.home'))

    return app
