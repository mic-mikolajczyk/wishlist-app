import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = 'app/static/uploads'
    # Internationalization settings
    BABEL_DEFAULT_LOCALE = 'pl'
    BABEL_DEFAULT_TIMEZONE = 'Europe/Warsaw'
    LANGUAGES = ['pl', 'en']
