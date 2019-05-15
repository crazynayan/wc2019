from flask import render_template, request, url_for
from flask_login import login_required
from app.main import bp
from app.main.game_transactions import *
from config import Config


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


@bp.route('/players')
def available_players():
    template = 'available.html'
    title = 'Players'
    direction = request.args.get('direction', FirestorePage.NEXT_PAGE, type=int)
    start_id = request.args.get('start', '')
    end_id = request.args.get('end', '')
    page = available_players_view(Config.PER_PAGE, start=start_id, end=end_id, direction=direction)
    next_url = None
    prev_url = None
    if page.has_next:
        next_url = url_for('main.available_players', end=page.current_end.doc_id)
    if page.has_prev:
        prev_url = url_for('main.available_players', start=page.current_start.doc_id, direction=FirestorePage.PREV_PAGE)
    return render_template(template, title=title, players=page.items, next_url=next_url, prev_url=prev_url)