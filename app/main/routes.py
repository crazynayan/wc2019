from flask import render_template, request, url_for, flash, redirect, jsonify, g, current_app
from flask_login import login_required, current_user
from app.main import bp
from app.main.forms import BidForm, SearchForm
from app.main.game_transactions import *
from config import Config


@bp.before_request
def before_request():
    game = Game.read()
    if game is None:
        game = Game.init_game()
    g.game = game
    if current_user.is_authenticated:
        g.search_form = SearchForm()
    if current_app and current_app.config.get('TESTING'):
        g.testing = True
    else:
        g.testing = False


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
@login_required
def purchased_players(username):
    template = 'purchased.html'
    title = 'Players'
    data = purchased_players_view(username)
    return render_template(template, title=title, players=data['players'], summary=data['summary'])


@bp.route('/available')
@login_required
def available_players():
    template = 'available.html'
    title = 'Players'
    direction = request.args.get('direction', FirestorePage.NEXT_PAGE, type=int)
    start_id = request.args.get('start', '')
    end_id = request.args.get('end', '')
    page = available_players_view(Config.PER_PAGE, start=start_id, end=end_id, direction=direction)
    if not page:
        return render_template(template, title=title)
    next_url = None
    prev_url = None
    if page.has_next:
        next_url = url_for('main.available_players', end=page.current_end.doc_id)
    if page.has_prev:
        prev_url = url_for('main.available_players', start=page.current_start.doc_id, direction=FirestorePage.PREV_PAGE)
    return render_template(template, title=title, players=page.items, next_url=next_url, prev_url=prev_url)


@bp.route('/players/<player_id>')
@login_required
def player_profile(player_id):
    template = 'player.html'
    player = player_view(player_id)
    title = player.name
    return render_template(template, title=title, player=player)


@bp.route('/bid', methods=['GET', 'POST'])
@login_required
def bid_player():
    template = 'bid.html'
    title = 'Bid'
    if not g.game.bid_in_progress:
        flash("No bid in progress")
        return redirect(url_for('main.index'))
    bid = Bid.query_first(player_name=g.game.player_in_bidding)
    if bid.has_bid(current_user.username):
        flash(f"You have already bid. Please wait for other {g.game.user_to_bid} users to bid.")
        return redirect(url_for('main.available_players'))
    player = Player.read(bid.doc_id)
    bid_form = BidForm(current_user.balance)
    pending = [User.read(username).name for username in g.game.users_to_bid]
    if not bid_form.validate_on_submit():
        if bid_form.amount.errors:
            for error in bid_form.amount.errors:
                flash(error)
        return render_template(template, title=title, bid=bid, form=bid_form, player=player, pending=pending)
    amount = bid_form.amount.data if bid_form.amount.data else Bid.PASS
    accept_bid(bid, current_user, amount)
    flash(f'Your bid for {bid.player_name} was submitted.')
    return redirect(url_for('main.available_players'))


@bp.route('/bids')
@login_required
def show_bids():
    template = 'bids.html'
    title = 'Bids'
    direction = request.args.get('direction', FirestorePage.NEXT_PAGE, type=int)
    start_id = request.args.get('start', '')
    end_id = request.args.get('end', '')
    page = bids_view(Config.PER_PAGE, start=start_id, end=end_id, direction=direction)
    if not page:
        return render_template(template, title=title)
    next_url = None
    prev_url = None
    if page.has_next:
        next_url = url_for('main.show_bids', end=page.current_end.doc_id)
    if page.has_prev:
        prev_url = url_for('main.show_bids', start=page.current_start.doc_id, direction=FirestorePage.PREV_PAGE)
    return render_template(template, title=title, bids=page.items, next_url=next_url, prev_url=prev_url)


@bp.route('/game_status')
@login_required
def game_status():
    game_dict = g.game.to_dict()
    return jsonify(game_dict)


@bp.route('/players')
@login_required
def player_search():
    template = 'search.html'
    title = 'Players'
    if not g.search_form.validate():
        return redirect(url_for('main.home'))
    tags = g.search_form.q.data.lower().split(';')
    data = search_players_view(tags)
    if not data:
        data = {'players': None, 'summary': None}
    tags_help = dict()
    tags_help['countries'] = Country.CODES
    tags_help['types'] = ['opener', 'middle order', 'wicket keeper', 'allrounder', 'fast bowler', 'spin bowler']
    tags_help['others'] = ['backup', 'injury', 'captain']
    return render_template(template, title=title, players=data['players'],
                           tags=tags, summary=data['summary'], help=tags_help)
