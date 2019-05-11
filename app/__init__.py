from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from firebase_admin import initialize_app, credentials, get_app
from config import Config
from firestore_model import FirestoreModel

login = LoginManager()
login.login_view = 'auth.login'
bootstrap = Bootstrap()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    try:
        app.db_app = get_app(app.name)
    except ValueError:
        app.db_app = initialize_app(credentials.Certificate(config_class.GAC_KEY_PATH), name=app.name)

    FirestoreModel.init_db(app.db_app)

    login.init_app(app)
    bootstrap.init_app(app)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app


