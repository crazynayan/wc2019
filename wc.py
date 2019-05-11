from firebase_admin import firestore
from app import create_app
from app.models import User, Player, Game, Bid

app = create_app()


@app.shell_context_processor
def make_shell_context():
    return {
        'db': firestore.client(app.db_app),
        'User': User,
        'Player': Player,
        'Game': Game,
        'Bid': Bid,
    }
