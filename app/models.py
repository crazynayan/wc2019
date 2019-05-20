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
        self.score = 0
        self.bid_order = 0
        self.type = None
        self.tags = list()
        self.matches = 0
        self.runs = 0
        self.wickets = 0
        self.balls = 0
        self.catches = 0
        # Country related fields
        self.country = None
        self.country_code = None
        self.bg_color = 'white'
        self.color = 'black'
        self.rank = 0

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
        return round(overs + (balls * 0.1), 1)

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
    def catches_per_match(self):
        if self.matches == 0:
            return 0
        return round(self.catches / self.matches, 2)

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

    @property
    def matches_to_play(self):
        if self.rank <= 0:
            return 0
        matches = 9
        if self.rank <= 4:
            matches += 1
            if self.rank <= 2:
                matches += 1
        return matches

    @property
    def playing_xi(self):
        probability = 0.8
        if 'captain' in self.tags:
            probability = 1
        elif 'backup' in self.tags:
            probability = 0.5
        return probability

    @property
    def value(self):
        if self.matches == 0:
            return 10
        points_per_match = self.runs_per_match * 0.5 + self.wickets_per_match * 10 + self.catches_per_match * 4
        points = points_per_match * self.matches_to_play
        # Adjust based on probability in playing XI
        points *= self.playing_xi
        # Adjust based on curve of number of matches played (1 match 60%, 50 matches 90%, >=100 matches 100%)
        adjustment_factor = 1 - 0.00004 * (100 - min(self.matches, 100)) ** 2
        points *= adjustment_factor
        return round(points)


class Game(FirestoreModel):
    COLLECTION = 'games'
    DEFAULT = 'user_count'
    SINGLE_ID = '1'

    def __init__(self, default=0):
        super().__init__(default)
        self.doc_id = self.SINGLE_ID
        # Initial after user upload
        self.user_count = 0
        self.total_balance = 0
        # Initialize after player upload
        self.player_count = 0
        self.player_to_bid = 0
        self.remaining_value = 0
        # Game status
        self.bid_in_progress = False
        self.player_in_bidding = None
        self.user_to_bid = 0  # Initialize to user_count when a player enters bidding, Decremented for every bid
        self.users_to_bid = list()
        self.last_player = None
        self.last_winner = None
        self.last_price = 0

    def create(self):
        return self.update()

    @classmethod
    def read(cls, doc_id=None):
        return super().read(cls.SINGLE_ID)

    @property
    def avg_player_bid(self):
        estimate = self.total_balance / self.player_to_bid if self.player_to_bid > 0 else 0
        if self.bid_in_progress and self.remaining_value > 0:
            player_value = Player.query_first(name=self.player_in_bidding).value
            estimate = self.total_balance * player_value / self.remaining_value
        return min(int(estimate), User.INITIAL_BUDGET, self.total_balance)

    # Should only be called after creating all users in db
    def set_user_count(self):
        users = User.get_all()
        self.user_count = len(users)
        self.total_balance = sum([user.balance for user in users])
        self.update()

    # Should only be called after creating all players in db
    def set_player_count(self):
        players = Player.get_all()
        self.player_count = len(players)
        self.player_to_bid = self.player_count
        self.remaining_value = sum([player.value for player in players])
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


class Country:
    CODES = ['eng', 'ind', 'nz', 'sa', 'aus', 'pak', 'sl', 'wi', 'ban', 'afg']
    DATA = {
        'eng': {'name': 'England', 'rank': 1, 'color': 'crimson', 'bg_color': 'navy'},
        'ind': {'name': 'India', 'rank': 2, 'color': 'darkorange', 'bg_color': 'dodgerblue'},
        'sa': {'name': 'South Africa', 'rank': 3, 'color': 'yellow', 'bg_color': 'forestgreen'},
        'nz': {'name': 'New Zealand', 'rank': 4, 'color': 'white', 'bg_color': 'black'},
        'aus': {'name': 'Australia', 'rank': 5, 'color': 'green', 'bg_color': 'yellow'},
        'pak': {'name': 'Pakistan', 'rank': 6, 'color': 'gold', 'bg_color': 'darkgreen'},
        'ban': {'name': 'Bangladesh', 'rank': 7, 'color': 'crimson', 'bg_color': 'olivedrab'},
        'wi': {'name': 'West Indies', 'rank': 8, 'color': 'yellow', 'bg_color': 'maroon'},
        'sl': {'name': 'Sri Lanka', 'rank': 9, 'color': 'yellow', 'bg_color': 'mediumblue'},
        'afg': {'name': 'Afghanistan', 'rank': 10, 'color': 'crimson', 'bg_color': 'deepskyblue'},
    }

    def __init__(self, code):
        if code.lower() in self.CODES:
            self.code = code.lower()
            self.init_data()
            return
        # Check if country name is passed instead of country code
        name = code
        country_list = [code for code in self.DATA if self.DATA[code]['name'].lower() == name.lower()]
        if country_list:
            self.code = country_list[0]
            self.init_data()
            return
        # Country is not valid
        self.code = None
        self.name = None
        self.rank = None
        self.color = None
        self.bg_color = None
        return

    def init_data(self):
        if not self.code or self.code not in self.CODES:
            return
        self.name = self.DATA[self.code]['name']
        self.rank = self.DATA[self.code]['rank']
        self.color = self.DATA[self.code]['color']
        self.bg_color = self.DATA[self.code]['bg_color']
        return
