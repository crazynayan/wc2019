from flask import render_template
from flask_login import login_required
from app.main import bp
from app.main.game_transactions import *


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    template = 'index.html'
    title = 'Home'
    users = ranked_users()
    return render_template(template, title=title, users=users)
