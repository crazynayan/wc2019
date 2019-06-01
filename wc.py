from firebase_admin import firestore
from app import create_app, cli
from app.models import User, Player, Game, Bid
from config import config


app = create_app(config.__class__)
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
