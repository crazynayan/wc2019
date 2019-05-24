import os
from firebase_admin import firestore
from app import create_app, cli
from app.models import User, Player, Game, Bid
from config import TestConfig

if os.environ.get('WC_ENVIRONMENT') == 'dev':
    app = create_app(TestConfig)
else:
    app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context():
    return {
        'db': firestore.client(app.db_app),
        'User': User,
        'Player': Player,
        'Game': Game,
        'Bid': Bid,
    }
