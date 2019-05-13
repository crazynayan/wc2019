import unittest
from app.main.game_transactions import *
from app import create_app
from app.models import User, Player, Game, Bid
from config import Config


class TestConfig(Config):
    TESTING = True
    GAC_KEY_PATH = 'test-key.json'


class UserTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        User.delete_all()
        Player.delete_all()
        Game.delete_all()
        Bid.delete_all()

    def tearDown(self) -> None:
        # User.delete_all()
        # Player.delete_all()
        # Game.delete_all()
        # Bid.delete_all()
        self.app_context.pop()

    def test_user_create(self):
        # Setup a user and test_user dictionary
        user = User('Vinayak', 'vp')
        test_user_dict = {
            'username': 'vp',
            'name': 'Vinayak',
            'balance': User.INITIAL_BUDGET,
            'points': 0.0,
            'color': 'black',
            'bg_color': 'white',
            'player_count': 0,
            'password_hash': None,
        }

        # Create a user
        user = user.create()

        # Read the user from db and check if it is the same
        db_user = User.read(user.doc_id)
        self.assertTrue(db_user, f'Doc Id: {user.username} not found in the db')
        self.assertDictEqual(test_user_dict, db_user.to_dict())

    def test_user_update(self):
        # Setup a user and test_user
        user = User('Purvi', 'pz')
        test_user = User('Purvi', 'pz')

        # Add it to the database with the username as the doc id
        user.update(user.username)

        # Read it from the database back
        db_user = User.read(user.username)
        self.assertTrue(db_user, f'Doc Id: {user.username} not found in the db')

        # Check if the test copy and the db copy is the same
        self.assertDictEqual(test_user.to_dict(), db_user.to_dict())

        # Update an attribute and check again
        user.name = 'Purvi Zaveri'
        test_user.name = 'Purvi Zaveri'
        user.update(user.username)
        db_user.refresh()
        self.assertTrue(db_user, f'Doc Id: {user.username} not found in the db')
        self.assertDictEqual(test_user.to_dict(), db_user.to_dict())

    def test_user_get_all(self):
        # Setup users and test_users
        users = dict()
        test_users = dict()
        names = {
            'Aarti': 'ak',
            'Manisha': 'ma',
            'Deepa': 'dm',
            'Sandeep': 'sb',
        }
        for name in names:
            user = User(name, names[name])
            users[name] = user
            test_users[name] = user

        # Add them to the database
        for name in names:
            users[name].update(users[name].username)

        # Get all users and check if the added users match
        db_users = User.get_all()
        for db_user in db_users:
            if db_user.name in names:
                self.assertDictEqual(test_users[db_user.name].to_dict(), db_user.to_dict())

    def test_query(self):
        # Setup users and test_users
        users = dict()
        test_users = dict()
        names = {
            'Aarti  ': {'username': 'ak', 'player_count': 5, 'balance': 5000, 'found': True},
            'Manisha': {'username': 'ma', 'player_count': 3, 'balance': 5000, 'found': False},
            'Deepa  ': {'username': 'dm', 'player_count': 5, 'balance': 5000, 'found': True},
            'Sandeep': {'username': 'sb', 'player_count': 1, 'balance': 1000, 'found': False},
        }
        for name in names:
            user = User(name, names[name]['username'])
            user.player_count = names[name]['player_count']
            user.balance = names[name]['balance']
            users[name] = user
            if names[name]['found']:
                test_users[name] = user

        # Add them to the database
        for name in names:
            users[name].create()

        # Get all users and check if the added users match
        db_users = User.query(player_count=5, balance=5000)
        self.assertEqual(len(test_users), len(db_users))
        for db_user in db_users:
            self.assertTrue(db_user.name in test_users)
            self.assertDictEqual(test_users[db_user.name].to_dict(), db_user.to_dict())

        # Ensure empty query is working
        db_users = User.query(player_count=100)
        self.assertEqual(0, len(db_users))

        # Test query_first
        name = 'Manisha'
        manisha = User(name, names[name]['username'])
        manisha.player_count = names[name]['player_count']
        manisha.balance = names[name]['balance']
        db_user = User.query_first(player_count=3, balance=5000)
        self.assertDictEqual(manisha.to_dict(), db_user.to_dict())

        # Ensure empty query_first is working
        db_user = User.query_first(player_count=3, balance=1000)
        self.assertFalse(db_user)

    def test_order_by(self):
        user_list = [
            {'name': 'Manisha', 'username': 'ma', 'points': 100, 'balance': 15, 'player_count': 3},
            {'name': 'Sneha', 'username': 'sy', 'points': 90, 'balance': 7, 'player_count': 3},
            {'name': 'Nayan', 'username': 'nz', 'points': 100, 'balance': 3, 'player_count': 1},
            {'name': 'Faisal', 'username': 'fa', 'points': 100, 'balance': 10, 'player_count': 3},
            {'name': 'Avinash', 'username': 'ag', 'points': 110, 'balance': 7, 'player_count': 3},
        ]
        test_list = [
            {'name': 'Avinash', 'username': 'ag', 'points': 110, 'balance': 7, 'player_count': 3},
            {'name': 'Manisha', 'username': 'ma', 'points': 100, 'balance': 15, 'player_count': 3},
            {'name': 'Faisal', 'username': 'fa', 'points': 100, 'balance': 10, 'player_count': 3},
            {'name': 'Nayan', 'username': 'nz', 'points': 100, 'balance': 3, 'player_count': 1},
            {'name': 'Sneha', 'username': 'sy', 'points': 90, 'balance': 7, 'player_count': 3},
        ]
        test_users = list()
        for user in user_list:
            User.from_dict(user).create()
        for test_user in test_list:
            test_users.append(User.from_dict(test_user))

        db_users = User.order_by(('points', User.ORDER_DESCENDING), ('balance', User.ORDER_DESCENDING))
        for index, db_user in enumerate(db_users):
            self.assertDictEqual(test_users[index].to_dict(), db_user.to_dict())


class GameTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        User.delete_all()
        Player.delete_all()
        Game.delete_all()
        Bid.delete_all()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_game_setup(self):
        # Setup user, player, game
        sneha = User('Sneha Yadgire', 'sy')
        manisha = User('Manisha Auti', 'ma')

        rohit = Player('Rohit Sharma')

        # Add them in db & refresh game status
        sneha.create()
        manisha.create()
        rohit.create()
        game = Game.init_game()

        # Read game and test
        self.assertEqual(game.player_count, 1)
        self.assertEqual(game.user_count, 2)
        self.assertEqual(game.avg_player_bid, User.INITIAL_BUDGET)
        self.assertEqual(rohit.status, Player.AVAILABLE)

    def test_player_purchase(self):
        # Setup user, player, game
        sneha = User('Sneha Yadgire', 'sy')
        manisha = User('Manisha Auti', 'ma')

        rohit = Player('Rohit Sharma')
        winner = {
            'name': sneha.name,
            'points': sneha.points,
        }
        winner_username = sneha.username
        players = ['p2', 'p3', 'p4', 'p5']

        # Add them in db
        sneha.create()
        manisha.create()
        rohit.create()
        for _, name in enumerate(players):
            player = Player(name)
            player.create()

        # Init game and test setup
        game = Game.init_game()
        # game.refresh()
        self.assertEqual(len(players) + 1, game.player_count)
        self.assertEqual(int(10000 * 2 / (len(players) + 1)), game.avg_player_bid)

        # Purchase Player
        rohit.refresh()
        sneha.refresh()
        purchase_player(rohit, sneha, 2000)

        # Refresh the game state after purchase
        game.refresh()
        rohit.refresh()
        sneha.refresh()

        # Test after purchase player
        self.assertEqual(18000, game.total_balance)
        self.assertEqual(len(players), game.player_to_bid)
        self.assertFalse(game.player_in_bidding)
        self.assertEqual(0, game.user_to_bid)
        self.assertEqual(rohit.name, game.last_player)
        self.assertEqual(sneha.name, game.last_winner)
        self.assertEqual(2000, game.last_price)
        self.assertEqual(8000, sneha.balance)
        self.assertEqual(1, sneha.player_count)
        self.assertEqual(Player.PURCHASED, rohit.status)
        self.assertDictEqual(winner, rohit.owner)
        self.assertEqual(winner_username, rohit.owner_username)
        self.assertEqual(2000, rohit.price)
        self.assertEqual(int(18000 / len(players)), game.avg_player_bid)

    def test_update_points(self):
        # Setup users and players
        user_map = {
            'nu': {'name': 'Nisha', 'points': 300},
            'pp': {'name': 'Pranay', 'points': 210.5},
            'nz': {'name': 'Nayan', 'points': 209.0},
            'rg': {'name': 'Raj', 'points': 113.5},
        }
        player_list = [
            {'name': 'Rohit Sharma', 'score': 60.5, 'owner': user_map['nu'], 'owner_username': 'nu'},
            {'name': 'Shikhar Dhawan', 'score': 100.0},
            {'name': 'Virat Kohli', 'score': 245.5, 'owner': user_map['pp'], 'owner_username': 'pp'},
            {'name': 'Hardik Pandya', 'score': 251, 'owner': user_map['rg'], 'owner_username': 'rg'},
            {'name': 'Jaspreet Bumrah', 'score': 151, 'owner': user_map['nu'], 'owner_username': 'nu'},
        ]
        users = list()
        players = list()
        for username, owner in user_map.items():
            db_user = User(owner['name'], username)
            db_user.points = owner['points']
            users.append(db_user)
        for _, player in enumerate(player_list):
            players.append(Player.from_dict(player))

        # Add them in db
        for user in users:
            user.create()
        for player in players:
            player.create()

        # Init points and check for 0 points
        # init_user_points()
        # db_users = User.get_all()
        # for db_user in db_users:
        #     self.assertEqual(0, db_user.points)

        # Sync points and check
        sync_player_user_points()
        user_points = {
            'nu': 211.5,
            'pp': 245.5,
            'nz': 0,
            'rg': 251,
        }

        db_users = User.get_all()
        for db_user in db_users:
            self.assertEqual(user_points[db_user.username], db_user.points)

        db_players = Player.get_all()
        for db_player in db_players:
            if db_player.owner:
                msg = f"{db_player.name}: {db_player.owner['name']} points mismatch."
                self.assertEqual(user_points[db_player.owner_username], db_player.owner['points'], msg)

        # Update score and sync points
        score_map = [
            {'player': 'Rohit Sharma', 'score': 10},
            {'player': 'Shikhar Dhawan', 'score': 15},
            {'player': 'Virat Kohli', 'score': 20.5},
            {'player': 'Hardik Pandya', 'score': 25},
            {'player': 'Jaspreet Bumrah', 'score': 30},
        ]
        user_points = {
            'nu': 40.0,
            'pp': 20.5,
            'nz': 0,
            'rg': 25,
        }
        self.assertTrue(Player.update_scores(score_map))
        sync_player_user_points()

        db_users = User.get_all()
        for db_user in db_users:
            self.assertEqual(user_points[db_user.username], db_user.points)

        db_players = Player.get_all()
        for db_player in db_players:
            if db_player.owner:
                msg = f"{db_player.name}: {db_player.owner['name']} points mismatch."
                self.assertEqual(user_points[db_player.owner_username], db_player.owner['points'], msg)

        # Check empty score_map
        self.assertFalse(Player.update_scores({}))

    def test_sorted_player_view(self):
        # Setup players and users in db
        player_list = [
            {'name': 'Rohit Sharma', 'score': 60.5},
            {'name': 'Shikhar Dhawan', 'score': 100.0},
            {'name': 'Virat Kohli', 'score': 245.5},
            {'name': 'Hardik Pandya', 'score': 251},
            {'name': 'Jaspreet Bumrah', 'score': 151},
        ]
        user_list = [
            {'username': 'nz', 'name': 'Nayan'},
            {'username': 'pp', 'name': 'Pranay'},
        ]
        test_player_list = [
            {
                'name': 'Hardik Pandya', 'score': 251,
                'owner_username': 'pp', 'owner': {'name': 'Pranay', 'points': 657.0},
                'status': Player.PURCHASED, 'price': 350,
            },
            {
                'name': 'Virat Kohli', 'score': 245.5,
                'owner_username': 'pp', 'owner': {'name': 'Pranay', 'points': 657.0},
                'status': Player.PURCHASED, 'price': 350,
            },
            {
                'name': 'Shikhar Dhawan', 'score': 100.0,
                'owner_username': 'pp', 'owner': {'name': 'Pranay', 'points': 657.0},
                'status': Player.PURCHASED, 'price': 350,
            },
            {
                'name': 'Rohit Sharma', 'score': 60.5,
                'owner_username': 'pp', 'owner': {'name': 'Pranay', 'points': 657.0},
                'status': Player.PURCHASED, 'price': 350,
            },
        ]
        test_players = list()
        for player in player_list:
            Player.from_dict(player).create()
        for user in user_list:
            User.from_dict(user).create()
        for player in test_player_list:
            test_players.append(Player.from_dict(player))

        # Purchase players
        nayan = User.read('nz')
        pranay = User.read('pp')
        players = Player.get_all()
        game = Game.init_game()
        for player in players:
            if player.name == 'Jaspreet Bumrah':
                purchase_player(player, nayan, 300)
            else:
                purchase_player(player, pranay, 350)

        # Refresh & Check purchase players
        game.refresh()
        nayan.refresh()
        pranay.refresh()
        self.assertEqual(0, game.user_to_bid)
        self.assertEqual(1, nayan.player_count)
        self.assertEqual(4, pranay.player_count)

        # Get pranay player view and check
        db_players = Player.order_by(('score', Player.ORDER_DESCENDING), query={'owner_username': 'pp'})
        for index, db_player in enumerate(db_players):
            self.assertDictEqual(test_players[index].to_dict(), db_player.to_dict())


class BidTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        User.delete_all()
        Player.delete_all()
        Game.delete_all()
        Bid.delete_all()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_bid(self):
        # Setup players, users and game in db
        player_list = [
            {'name': 'Rohit Sharma', 'bid_order': 2},
            {'name': 'Shikhar Dhawan', 'bid_order': 4},
            {'name': 'Virat Kohli', 'bid_order': 1},
            {'name': 'Hardik Pandya', 'bid_order': 3},
            {'name': 'Jaspreet Bumrah', 'bid_order': 5},
        ]
        user_list = [
            {'username': 'nz', 'name': 'Nayan'},
            {'username': 'pp', 'name': 'Pranay'},
            {'username': 'sa', 'name': 'Shraddha'},
            {'username': 'rg', 'name': 'Raj'},
        ]
        for player in player_list:
            Player.from_dict(player).create()
        for user in user_list:
            User.from_dict(user).create()
        game = Game.init_game()

        # Invite bid and check
        bid = invite_bid()
        game.refresh()
        self.assertIsInstance(bid, Bid)
        self.assertEqual('Virat Kohli', game.player_in_bidding)
        self.assertEqual(4, game.user_to_bid)
        self.assertEqual(5, game.player_to_bid)
        self.assertEqual(Player.BIDDING, Player.query_first(name='Virat Kohli').status)
        self.assertTrue(game.bid_in_progress)
        self.assertEqual(1, bid.bid_order)

        # One Bid on 1st player
        bid_result = accept_bid(bid, User.query_first(username='nz'), 1500)
        bid.refresh()
        game.refresh()
        self.assertEqual(Bid.SUCCESS, bid_result)
        self.assertIn('nz', bid.usernames)
        self.assertTrue(bid.has_bid('nz'))
        self.assertEqual(3, game.user_to_bid)
        self.assertIn({'username': 'nz', 'amount': 1500}, bid.bid_map)

        # Two more bid on 1st player
        bid_result = accept_bid(bid, User.query_first(username='pp'), 1200)
        bid.refresh()
        game.refresh()
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='rg'), 1550)
        bid.refresh()
        game.refresh()
        self.assertEqual(Bid.SUCCESS, bid_result)
        self.assertNotIn('sa', bid.usernames)
        self.assertEqual(1, game.user_to_bid)
        self.assertFalse(bid.is_bid_complete(game.user_count))
        self.assertEqual(Bid.SUCCESS, bid_result)
        self.assertFalse(bid.has_bid('sa'))

        # Last player and check winner
        bid_result = accept_bid(bid, User.query_first(username='sa'), 1350)
        bid.refresh()
        game.refresh()
        self.assertEqual('Raj', game.last_winner)
        self.assertEqual('Virat Kohli', game.last_player)
        self.assertEqual(1550, game.last_price)
        self.assertEqual(Player.PURCHASED, Player.query_first(name='Virat Kohli').status)
        self.assertEqual('rg', Player.query_first(name='Virat Kohli').owner_username)
        self.assertEqual('rg', bid.winner)
        self.assertEqual(1550, bid.winning_price)

        # Check if the next player is properly invited for bid
        bid = bid_result
        self.assertIsInstance(bid, Bid)
        self.assertEqual('Rohit Sharma', game.player_in_bidding)
        self.assertEqual(4, game.user_to_bid)
        self.assertEqual(4, game.player_to_bid)
        self.assertEqual(Player.BIDDING, Player.query_first(name='Rohit Sharma').status)
        self.assertTrue(game.bid_in_progress)
        self.assertEqual(2, bid.bid_order)

        # Pass the player
        bid_result = accept_bid(bid, User.query_first(username='sa'), Bid.PASS)
        game.refresh()
        bid.refresh()
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='rg'))
        game.refresh()
        bid.refresh()
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='nz'), Bid.PASS)
        game.refresh()
        bid.refresh()
        self.assertEqual(Bid.SUCCESS, bid_result)
        self.assertEqual(1, game.user_to_bid)
        bid_result = accept_bid(bid, User.query_first(username='pp'))
        game.refresh()
        bid.refresh()
        self.assertIsInstance(bid_result, Bid)
        self.assertEqual('Unsold', game.last_winner)
        self.assertEqual('Rohit Sharma', game.last_player)
        self.assertEqual(0, game.last_price)
        self.assertEqual(Player.UNSOLD, Player.query_first(name='Rohit Sharma').status)
        self.assertIsNone(Player.query_first(name='Rohit Sharma').owner_username)
        self.assertIsNone(bid.winner)
        self.assertEqual(0, bid.winning_price)

        # Check next player
        bid = bid_result
        self.assertEqual('Hardik Pandya', game.player_in_bidding)
        self.assertEqual(4, game.user_to_bid)
        self.assertEqual(3, game.player_to_bid)
        self.assertEqual(Player.BIDDING, Player.query_first(name='Hardik Pandya').status)
        self.assertTrue(game.bid_in_progress)
        self.assertEqual(3, bid.bid_order)

        # Check accept bid errors
        self.assertEqual(Bid.ERROR_INVALID_AMOUNT, accept_bid(bid, None, 0))
        self.assertEqual(Bid.ERROR_SYSTEM, accept_bid(bid, None))
        test_user = User('Nayan', 'nz')
        test_user.username = None
        self.assertEqual(Bid.ERROR_SYSTEM, accept_bid(bid, test_user))
        test_user.username = 'nz'
        self.assertEqual(Bid.ERROR_SYSTEM, accept_bid(None, test_user))
        test_bid = Bid('No Player')
        self.assertEqual(Bid.ERROR_SYSTEM, accept_bid(test_bid, test_user))
        test_bid = Bid.read(bid.doc_id)
        test_bid.player_name = 'Invalid Player'
        self.assertEqual(Bid.ERROR_PLAYER_NOT_FOUND, accept_bid(test_bid, test_user))
        test_bid.player_name = 'Rohit Sharma'
        self.assertEqual(Bid.ERROR_PLAYER_NOT_INVITED_TO_BID, accept_bid(test_bid, test_user))
        self.assertEqual(Bid.ERROR_NO_BALANCE, accept_bid(bid, test_user, User.INITIAL_BUDGET + 100))
        self.assertEqual(Bid.SUCCESS, accept_bid(bid, test_user))
        self.assertEqual(Bid.ERROR_ALREADY_BID, accept_bid(bid, test_user))

        # Let other players bid
        bid_result = accept_bid(bid, User.query_first(username='pp'), 2000)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='rg'), 2100)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='sa'), 2500)
        self.assertIsInstance(bid_result, Bid)
        self.assertEqual('sa', Player.query_first(name=bid.player_name).owner_username)

        # Bid for remaining 2 players
        bid = bid_result
        bid_result = accept_bid(bid, User.query_first(username='nz'), 2000)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='pp'), 2600)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='rg'), 2700)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='sa'), 2300)
        self.assertIsInstance(bid_result, Bid)
        self.assertEqual('rg', Player.query_first(name=bid.player_name).owner_username)
        self.assertEqual(2, User.query_first(username='rg').player_count)
        bid = bid_result
        bid_result = accept_bid(bid, User.query_first(username='nz'), 3000)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='pp'), 6000)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='rg'), 3500)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='sa'), 4000)
        self.assertEqual(Bid.ERROR_NO_MORE_PLAYERS, bid_result)
        game.refresh()
        self.assertEqual(0, game.player_to_bid)
        self.assertIsNone(game.player_in_bidding)
        self.assertFalse(game.bid_in_progress)
        self.assertEqual(0, game.user_to_bid)

