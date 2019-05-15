import csv
from firebase_admin import firestore
from flask import current_app
from firestore_model import FirestorePage
from app.models import Game, User, Player, Bid



@firestore.transactional
def purchase_player_transaction(transaction, player, user=None, amount=0):
    player_ref, player_snapshot = player.get_doc(transaction)
    user_ref = None
    user_snapshot = None
    user_updates = None
    if user:
        user_ref, user_snapshot = user.get_doc(transaction)
        if not user_snapshot:
            return False
    game = Game.read()
    if not game:
        game = Game.init_game()
    game_ref, game_snapshot = game.get_doc(transaction)
    if not player_snapshot or not game_snapshot:
        return False
    if user_snapshot:
        player_updates = {
            'status': player.PURCHASED,
            'owner_username': user_snapshot.get('username'),
            'owner': {
                'name': user_snapshot.get('name'),
                'points': user_snapshot.get('points') + player_snapshot.get('score'),
            },
            'price': amount,
        }
        user_updates = {
            'balance': user_snapshot.get('balance') - amount,
            'player_count': user_snapshot.get('player_count') + 1,
        }
        last_winner = user_snapshot.get('name')
    else:
        player_updates = {
            'status': player.UNSOLD
        }
        last_winner = 'Unsold'
        amount = 0
    game_updates = {
        'total_balance': game_snapshot.get('total_balance') - amount,
        'player_in_bidding': None,
        'player_to_bid': game_snapshot.get('player_to_bid') - 1,
        'user_to_bid': 0,
        'last_player': player_snapshot.get('name'),
        'last_winner': last_winner,
        'last_price': amount,
        'bid_in_progress': False,
    }
    if user_updates:
        transaction.update(user_ref, user_updates)
    transaction.update(player_ref, player_updates)
    transaction.update(game_ref, game_updates)
    return True


def purchase_player(player, user, amount):
    db = firestore.client(current_app.db_app)
    transaction = db.transaction()
    if purchase_player_transaction(transaction, player, user, amount):
        return update_user_points_transaction(transaction, user)
    return False


@firestore.transactional
def update_user_points_transaction(transaction, user):
    players = Player.query(owner_username=user.username)
    owning_players = list()
    points = 0
    for player in players:
        player_ref, player_snapshot = player.get_doc(transaction)
        points += player_snapshot.get('score')
        player_map = {
            'player_ref': player_ref,
            'owner': player_snapshot.get('owner'),
        }
        owning_players.append(player_map)
    if points == 0:
        return False
    # Update the user points
    user_ref, user_snapshot = user.get_doc(transaction)
    user_updates = {
        'points': points,
    }
    transaction.update(user_ref, user_updates)
    # Update points of each player owned by user
    for player_map in owning_players:
        owner = player_map['owner']
        owner['points'] = points
        player_updates = {
            'owner': owner
        }
        transaction.update(player_map['player_ref'], player_updates)
    return True


def init_user_points():
    users = User.get_all()
    User.init_batch()
    for user in users:
        user.points = 0
        user.update_batch()
    User.commit_batch()


def sync_player_user_points():
    # This function needs to be called after scores.csv has been updated
    init_user_points()
    users = User.get_all()
    db = firestore.client(current_app.db_app)
    transaction = db.transaction()
    for user in users:
        update_user_points_transaction(transaction, user)


@firestore.transactional
def invite_bid_transaction(transaction, player):
    player_ref, player_snapshot = player.get_doc(transaction)
    game = Game.read()
    if not game:
        game = Game.init_game()
    game_ref, game_snapshot = game.get_doc(transaction)
    # Validate
    if not player_snapshot or player_snapshot.get('status') != Player.AVAILABLE:
        return Bid.ERROR_PLAYER_NOT_AVAILABLE
    if game_snapshot.get('bid_in_progress'):
        return Bid.ERROR_BID_IN_PROGRESS
    bid = Bid(player_snapshot.get('name'))
    # Creation not in transaction is fine since it will only create the bid once
    bid = bid.create()
    player_updates = {
        'status': Player.BIDDING
    }
    game_updates = {
        'bid_in_progress': True,
        'user_to_bid': game_snapshot.get('user_count'),
        'player_in_bidding': player_snapshot.get('name'),
    }
    # Auto bid for zero balance
    zero_balance_users = User.query(balance=0)
    if zero_balance_users:
        bid_ref, bid_snapshot = bid.get_doc(transaction)
        for user in zero_balance_users:
            zero_bid = {
                'username': user.username,
                'amount': Bid.NO_BALANCE,
            }
            bid_updates = {
                'bid_map': bid_snapshot.get('bid_map').append(zero_bid),
                'usernames': bid_snapshot.get('usernames').append(user.usernames),
            }
            game_updates['user_to_bid'] -= 1
        transaction.update(bid_ref, bid_updates)
    transaction.update(player_ref, player_updates)
    transaction.update(game_ref, game_updates)
    return Bid.SUCCESS


@firestore.transactional
def accept_bid_transaction(transaction, bid, user, amount):
    if amount != Bid.PASS and amount < 1:
        return Bid.ERROR_INVALID_AMOUNT
    if not bid:
        return Bid.ERROR_SYSTEM
    bid_ref, bid_snapshot = bid.get_doc(transaction)
    game = Game.read()
    if not game:
        game = Game.init_game()
    game_ref, game_snapshot = game.get_doc(transaction)
    # Validate (Does NOT validate if the user exists in the db)
    if not bid_snapshot or not user or not user.username:
        return Bid.ERROR_SYSTEM
    if bid_snapshot.get('usernames') and user.username in bid_snapshot.get('usernames'):
        return Bid.ERROR_ALREADY_BID
    if user.balance < amount:
        return Bid.ERROR_NO_BALANCE
    player = Player.query_first(name=bid.player_name)
    if not player:
        return Bid.ERROR_PLAYER_NOT_FOUND
    if player.status != Player.BIDDING:
        return Bid.ERROR_PLAYER_NOT_INVITED_TO_BID
    user_bid = {
        'username': user.username,
        'amount': amount,
    }
    bid_list = [user_bid]
    if bid_snapshot.get('bid_map'):
        bid_list = bid_snapshot.get('bid_map')
        bid_list.append(user_bid)
    user_list = [user.username]
    if bid_snapshot.get('usernames'):
        user_list = bid_snapshot.get('usernames')
        user_list.append(user.username)
    bid_updates = {
        'bid_map': bid_list,
        'usernames': user_list,
    }
    game_updates = {
        'user_to_bid': game_snapshot.get('user_to_bid') - 1,
    }
    transaction.update(bid_ref, bid_updates)
    transaction.update(game_ref, game_updates)
    return Bid.SUCCESS


def accept_bid(bid, user, amount=Bid.PASS):
    db = firestore.client(current_app.db_app)
    transaction = db.transaction()
    bid_result = accept_bid_transaction(transaction, bid, user, amount)
    if bid_result <= 0:
        return bid_result
    bid.refresh()
    game = Game.read()
    if not bid.is_bid_complete(game.user_count):
        return Bid.SUCCESS
    # Determine Winner
    player = Player.query_first(name=bid.player_name)
    winning_bid = max(bid.bid_map, key=lambda bid_dict: bid_dict['amount'])
    if winning_bid['amount'] < 1:
        purchase_player_transaction(transaction, player)
    else:
        winner = User.query_first(username=winning_bid['username'])
        purchase_player_transaction(transaction, player, winner, winning_bid['amount'])
        bid.winner = winning_bid['username']
        bid.winning_price = winning_bid['amount']
        bid.update()
    # Invite another bid
    return invite_bid()


def invite_bid():
    db = firestore.client(current_app.db_app)
    transaction = db.transaction()
    available_players = available_players_view()
    if not available_players:
        return Bid.ERROR_NO_MORE_PLAYERS
    bid_result = invite_bid_transaction(transaction, available_players[0])
    if bid_result != Bid.SUCCESS:
        return bid_result
    bid = Bid.query_first(player_name=available_players[0].name)
    if not bid:
        return Bid.ERROR_SYSTEM
    return bid


def ranked_users_view():
    return User.order_by(('points', User.ORDER_DESCENDING), ('balance', User.ORDER_DESCENDING))


def purchased_players_view(username):
    return Player.order_by(('score', User.ORDER_DESCENDING), ('price', User.ORDER_DESCENDING),
                           query={'owner_username': username})


def available_players_view(per_page=None, start='', end='', direction=FirestorePage.NEXT_PAGE):
    if per_page is None or direction not in [FirestorePage.NEXT_PAGE, FirestorePage.PREV_PAGE]:
        return Player.order_by('bid_order', query=({'status': Player.AVAILABLE}))
    page = FirestorePage(per_page)
    if start:
        page.current_start = Player.read(start)
    if end:
        page.current_end = Player.read(end)
    page.want = direction
    page = Player.order_by('bid_order', query=({'status': Player.AVAILABLE}), page=page)
    if len(page.items) == 0:
        return None
    return page


class Upload:
    ACCEPTED_TYPES = [
        'users',
        'players',
        'scores',
    ]
    SUCCESS = 0
    ERROR_NOT_VALID_TYPE = -1
    ERROR_FILE_NOT_FOUND = -2
    ERROR_INVALID_HEADER = -3

    def __init__(self, upload_type=None):
        self.type = upload_type
        self.data_list = None

    def __call__(self, upload_type=None):
        if upload_type is not None:
            self.type = upload_type
        if not self.type or self.type not in self.ACCEPTED_TYPES:
            return self.ERROR_NOT_VALID_TYPE
        self.file_name = upload_type + '.csv'
        try:
            with open(self.file_name) as csv_file:
                self.data_list = list(csv.reader(csv_file))
        except FileNotFoundError:
            return self.ERROR_FILE_NOT_FOUND
        upload_function = 'upload_' + self.type
        return getattr(self, upload_function)()

    def upload_users(self):
        # Index of columns         0            1        2          3         4
        if self.data_list[0] != ['username', 'name', 'password', 'color', 'bg_color']:
            return self.ERROR_INVALID_HEADER
        User.delete_all()
        User.init_batch()
        for user_row in self.data_list[1:]:
            user = User(user_row[1].strip(), user_row[0].strip())
            user.set_password(user_row[2])
            user.color = user_row[3].strip().lower()
            user.bg_color = user_row[4].strip().lower()
            user.update_batch()
        User.commit_batch()
        return self.SUCCESS

    def upload_players(self):
        # Index of columns         0         1         2       3        4         5         6        7        8
        if self.data_list[0] != ['name', 'country', 'type', 'tags', 'matches', 'runs', 'wickets', 'balls', 'bid_order']:
            return self.ERROR_INVALID_HEADER
        Player.delete_all()
        Player.init_batch()
        for player_row in self.data_list[1:]:
            # if player_row[0] != 'Andre Russel':
            #     continue
            player = Player(player_row[0].strip())
            player.country = player_row[1].strip()
            player.type = player_row[2].strip()
            tags = [tag.strip().lower() for tag in player_row[3].split(';') if len(tag) > 0]
            tags.append(player.country.lower())
            tags.append(player.name.lower())
            if player.type.lower() not in player_row[3].lower():
                tags.append(player.type.lower())
            player.tags = tags
            try:
                player.matches = int(player_row[4])
            except ValueError:
                pass
            try:
                player.runs = int(player_row[5])
            except ValueError:
                pass
            try:
                player.wickets = int(player_row[6])
            except ValueError:
                pass
            try:
                player.balls = int(player_row[7])
            except ValueError:
                pass
            try:
                player.bid_order = int(player_row[8])
            except ValueError:
                pass
            player.update_batch()
        Player.commit_batch()
        return self.SUCCESS

    def upload_scores(self):
        pass

