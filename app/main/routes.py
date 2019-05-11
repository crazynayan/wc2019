from flask import render_template
from app.main import bp


@bp.route('/')
@bp.route('/index')
def index():
    template = 'index.html'
    title = 'Home'
    return render_template(template, title=title)
