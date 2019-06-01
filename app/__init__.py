from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap

from config import Config
from firestore_model import init_firestore_db

login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.db_app = init_firestore_db(config_class.GAC_KEY_PATH, app.name)

    login.init_app(app)
    bootstrap.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app


