
from firestore_model import FirestoreModel


class User(FirestoreModel):
    INITIAL_BUDGET = 10000
    COLLECTION = 'users'
    DEFAULT = 'name'

    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.username = name[:2] if len(name) >= 2 else None
        self.balance = self.INITIAL_BUDGET
        self.points = 0.0
        self.color = 'black'
        self.bg_color = 'white'
        self.player_count = 0

    def to_dict(self):
        return {
            'username': self.username,
            'name': self.name,
            'balance': self.balance,
            'points': self.points,
            'color': self.color,
            'bg_color': self.bg_color,
            'player_count': self.player_count
        }

    def create(self):
        if self.username is None:
            return None
        return self.update(self.username)


class Player(FirestoreModel):
    COLLECTION = 'players'
    DEFAULT = 'name'
    # Player status
    AVAILABLE = 'available'
    BIDDING = 'bidding'
    PURCHASED = 'purchased'
    UNSOLD = 'unsold'

    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.owner = None
        self.owner_username = None
        self.price = 0
        self.status = self.AVAILABLE
        self.country = None
        self.score = 0
        self.bid_order = 0

    def create(self):
        return self.update(self.name.replace(' ', '_'))

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
        self.last_player = None
        self.last_winner = None
        self.last_price = 0
        self.bid_in_progress = False

    def create(self):
        return super().update()

    def update(self, doc_id=None):
        return super().update()

    @classmethod
    def read(cls, doc_id=None):
        return super().read(cls.SINGLE_ID)

    @property
    def avg_player_bid(self):
        estimate = self.total_balance / self.player_to_bid if self.player_to_bid > 0 else 0
        return min(int(estimate), User.INITIAL_BUDGET, self.total_balance)

    # Should only be called after creating all users in db
    def set_user_count(self):
        self.user_count = len(User.get_all())
        self.total_balance = self.user_count * User.INITIAL_BUDGET
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

    def __init__(self, player_name):
        super().__init__(player_name)
        self.player_name = player_name
        self.bid_map = list()
        self.usernames = list()
        self.winner = None
        self.winning_price = 0
        self.bid_order = None
        player = Player.query_first(name=self.player_name)
        if player:
            self.bid_order = player.bid_order

    def create(self):
        return self.update(self.player_name.replace(' ', '_'))

    def has_bid(self, username):
        return username in self.usernames

    def is_bid_complete(self, user_count):
        if not self.usernames:
            return False
        return len(self.usernames) >= user_count


