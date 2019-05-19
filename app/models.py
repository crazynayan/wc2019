from os import path
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from firestore_model import FirestoreModel
from app import login


class User(UserMixin, FirestoreModel):
    INITIAL_BUDGET = 10000
    COLLECTION = 'users'
    DEFAULT = 'username'

    def __init__(self, username=None, name=None):
        super().__init__()
        self.username = username if username else '**'
        self.doc_id = username
        self.name = name if name else 'No Name'
        self.balance = self.INITIAL_BUDGET
        self.points = 0.0
        self.color = 'black'
        self.bg_color = 'white'
        self.player_count = 0
        self.password_hash = None

    def create(self):
        return self.update()

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.username


@login.user_loader
def load_user(username):
    return User.query_first(username=username)


class Player(FirestoreModel):
    COLLECTION = 'players'
    DEFAULT = 'name'
    # Player status
    AVAILABLE = 'available'
    BIDDING = 'bidding'
    PURCHASED = 'purchased'
    UNSOLD = 'unsold'

    def __init__(self, name=None):
        super().__init__(name)
        self.name = name if name else 'No Name'
        self.doc_id = self.name.replace(' ', '_').lower()
        self.owner = None
        self.owner_username = None
        self.price = 0
        self.status = self.AVAILABLE
        self.country = None
        self.score = 0
        self.bid_order = 0
        self.bg_color = 'white'
        self.color = 'black'
        self.type = None
        self.tags = list()
        self.matches = 0
        self.runs = 0
        self.wickets = 0
        self.balls = 0

    def create(self):
        return self.update()

    @classmethod
    def update_scores(cls, scores):
        if not scores or 'player' not in scores[0] or 'score' not in scores[0]:
            return False
        Player.init_batch()
        for score in scores:
            player = Player.query_first(name=score['player'])
            if player:
                player.score = score['score']
                player.update_batch()
        Player.commit_batch()
        return True

    @property
    def overs_per_match(self):
        if self.balls == 0 or self.matches == 0:
            return 0
        balls_per_match = round(self.balls / self.matches)
        overs = balls_per_match // 6
        balls = balls_per_match % 6
        return overs + (balls * 0.1)

    @property
    def runs_per_match(self):
        if self.matches == 0:
            return 0
        return round(self.runs / self.matches, 2)

    @property
    def wickets_per_match(self):
        if self.matches == 0:
            return 0
        return round(self.wickets / self.matches, 2)

    @property
    def image_file(self):
        if not self.doc_id:
            return None
        filenames = [
            self.doc_id + '.jpg',
            self.doc_id + '.png',
            self.doc_id + '.gif',
        ]
        for filename in filenames:
            if path.exists('app/static/' + filename):
                return filename
        return None


class Game(FirestoreModel):
    COLLECTION = 'games'
    DEFAULT = 'user_count'
    SINGLE_ID = '1'

    def __init__(self, default=0):
        super().__init__(default)
        self.doc_id = self.SINGLE_ID
        self.user_count = 0
        self.player_count = 0

        self.total_balance = 0  # Needs to be incremented at the same time as user_count
        self.player_to_bid = 0  # Needs to be incremented at the same time as player_count

        self.player_in_bidding = None
        self.user_to_bid = 0  # Initialize to user_count when a player enters bidding, Decremented for every bid
        self.users_to_bid = list()
        self.last_player = None
        self.last_winner = None
        self.last_price = 0
        self.bid_in_progress = False

    def create(self):
        return self.update()

    @classmethod
    def read(cls, doc_id=None):
        return super().read(cls.SINGLE_ID)

    @property
    def avg_player_bid(self):
        estimate = self.total_balance / self.player_to_bid if self.player_to_bid > 0 else 0
        return min(int(estimate), User.INITIAL_BUDGET, self.total_balance)

    # Should only be called after creating all users in db
    def set_user_count(self):
        users = User.get_all()
        self.user_count = len(users)
        self.total_balance = self.user_count * sum([user.balance for user in users])
        self.update()

    # Should only be called after creating all players in db
    def set_player_count(self):
        self.player_count = len(Player.get_all())
        self.player_to_bid = self.player_count
        self.update()

    @staticmethod
    def init_game():
        game = Game()
        game.create()
        game.set_user_count()
        game.set_player_count()
        game.refresh()
        return game


class Bid(FirestoreModel):
    COLLECTION = 'bids'
    DEFAULT = 'player_name'
    # Bid type
    NO_BALANCE = -2
    PASS = -1
    OWNED = -3
    # Accept Bid Result
    SUCCESS = 1
    ERROR_SYSTEM = -99
    ERROR_ALREADY_BID = -1
    ERROR_PLAYER_NOT_FOUND = -2
    ERROR_NO_BALANCE = -3
    ERROR_PLAYER_NOT_INVITED_TO_BID = -4
    ERROR_INVALID_AMOUNT = -5
    # Invite Bid Result
    # On Success returns the bid object
    ERROR_NO_MORE_PLAYERS = -11
    ERROR_PLAYER_NOT_AVAILABLE = -12
    ERROR_BID_IN_PROGRESS = -13

    def __init__(self, player_name=None):
        super().__init__(player_name)
        self.player_name = player_name if player_name else 'No Name'
        self.doc_id = self.player_name.replace(' ', '_').lower()
        self.bid_map = list()
        self.winner = None
        self.winning_price = 0
        self.bid_order = None
        player = Player.query_first(name=self.player_name)
        if player:
            self.bid_order = player.bid_order

    def create(self):
        return self.update()

    def has_bid(self, username):
        if not self.bid_map:
            return False
        usernames = [bd['username'] for bd in self.bid_map]
        return username in usernames

    def is_bid_complete(self, user_count):
        if not self.bid_map:
            return False
        return len(self.bid_map) >= user_count


