from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from firebase_admin import initialize_app, credentials, firestore
from config import Config

db = None
login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()


def create_app(config_class=Config):
    global db
    app = Flask(__name__)
    app.config.from_object(config_class)

    db_app = initialize_app(credentials.Certificate(config_class.GAC_KEY_PATH), name=app.name)
    db = firestore.client(db_app)

    login.init_app(app)
    bootstrap.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app


from app import models

