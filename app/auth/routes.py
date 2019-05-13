from flask import redirect, url_for, render_template, flash, request
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse
from app.models import User
from app.auth import bp
from app.auth.forms import LoginForm


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    template = 'login.html'
    title = 'Sign In'
    form = LoginForm()
    if not form.validate_on_submit():
        return render_template(template, title=title, form=form)
    # This is a POST request and the form is validated
    user = User.query_first(username=form.username.data)
    if user is None or not user.check_password(form.password.data):
        flash('Invalid username or password')
        return redirect(url_for('auth.login'))
    login_user(user=user)
    next_page = request.args.get('next')
    if not next_page or url_parse(next_page).netloc != '':
        next_page = url_for('main.index')
    return redirect(next_page)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))
