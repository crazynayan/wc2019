from flask import render_template
from flask_login import login_required
from app.main import bp
from app.main.game_transactions import *


@bp.route('/')
@bp.route('/index')
@bp.route('/users')
@login_required
def index():
    template = 'index.html'
    title = 'Home'
    users = ranked_users_view()
    return render_template(template, title=title, users=users)


@bp.route('/users/<username>/players')
def purchased_players(username):
    template = 'players.html'
    title = 'Players'
    players = purchased_players_view(username)
    return render_template(template, title=title, players=players)
