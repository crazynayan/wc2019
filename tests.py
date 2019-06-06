import unittest
import os
from random import randrange
from app.main.game_transactions import *
from app import create_app
from app.models import User, Player, Game, Bid, Country
from config import TestConfig


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
        self.app_context.pop()

    def test_user_create(self):
        # Setup a user and test_user dictionary
        user = User(name='Vinayak', username='vp')
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
        user = User(name='Purvi', username='pz')
        test_user = User(name='Purvi', username='pz')

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
            user = User(name=name, username=names[name])
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
            user = User(name=name, username=names[name]['username'])
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
        manisha = User(name=name, username=names[name]['username'])
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

        db_users = ranked_users_view()
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
        sneha = User(name='Sneha Yadgire', username='sy')
        manisha = User(name='Manisha Auti', username='ma')

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
        sneha = User(name='Sneha Yadgire', username='sy')
        manisha = User(name='Manisha Auti', username='ma')

        rohit = Player('Rohit Sharma')
        winner = {
            'name': sneha.name,
            'points': sneha.points,
            'color': 'black',
            'bg_color': 'white',
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
        self.assertEqual(sneha.username.upper(), game.last_winner)
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
            {'name': 'Jasprit Bumrah', 'score': 151, 'owner': user_map['nu'], 'owner_username': 'nu'},
        ]
        users = list()
        players = list()
        for username, owner in user_map.items():
            db_user = User(name=owner['name'], username=username)
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
        init_user_points()
        db_users = User.get_all()
        for db_user in db_users:
            self.assertEqual(0, db_user.points)

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
            {'player': 'Jasprit Bumrah', 'score': 30},
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
            {'name': 'Jasprit Bumrah', 'score': 151},
        ]
        user_list = [
            {'username': 'nz', 'name': 'Nayan'},
            {'username': 'pp', 'name': 'Pranay'},
        ]
        test_player_list = [
            {
                'name': 'Hardik Pandya', 'score': 251,
                'owner_username': 'pp',
                'owner': {'name': 'Pranay', 'points': 657.0, 'color': 'black', 'bg_color': 'white'},
                'status': Player.PURCHASED, 'price': 350,
            },
            {
                'name': 'Virat Kohli', 'score': 245.5,
                'owner_username': 'pp',
                'owner': {'name': 'Pranay', 'points': 657.0, 'color': 'black', 'bg_color': 'white'},
                'status': Player.PURCHASED, 'price': 350,
            },
            {
                'name': 'Shikhar Dhawan', 'score': 100.0,
                'owner_username': 'pp',
                'owner': {'name': 'Pranay', 'points': 657.0, 'color': 'black', 'bg_color': 'white'},
                'status': Player.PURCHASED, 'price': 350,
            },
            {
                'name': 'Rohit Sharma', 'score': 60.5,
                'owner_username': 'pp',
                'owner': {'name': 'Pranay', 'points': 657.0, 'color': 'black', 'bg_color': 'white'},
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
            if player.name == 'Jasprit Bumrah':
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
        data = purchased_players_view(pranay.username)
        for index, db_player in enumerate(data['players']):
            self.assertDictEqual(test_players[index].to_dict(), db_player.to_dict())
        self.assertEqual(657, data['summary']['score'])
        self.assertEqual(1400, data['summary']['price'])


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
            {'name': 'Jasprit Bumrah', 'bid_order': 5},
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
        self.assertNotIn('nz', game.users_to_bid)
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
        self.assertIn('sa', game.users_to_bid)
        self.assertEqual(1, game.user_to_bid)
        self.assertFalse(bid.is_bid_complete(game.user_count))
        self.assertEqual(Bid.SUCCESS, bid_result)
        self.assertFalse(bid.has_bid('sa'))

        # Last player and check winner
        bid_result = accept_bid(bid, User.query_first(username='sa'), 1350)
        bid.refresh()
        game.refresh()
        self.assertEqual('RG', game.last_winner)
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
        test_user = User(name='Nayan', username='nz')
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
        bid_result = accept_bid(bid, User.query_first(username='sa'), 10000)
        self.assertIsInstance(bid_result, Bid)
        self.assertEqual('sa', Player.query_first(name=bid.player_name).owner_username)

        # Bid for next player and check the auto zero bid for 'sa'
        bid = bid_result
        bid_result = accept_bid(bid, User.query_first(username='nz'), 2000)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='pp'), 2600)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='rg'), 2700)
        self.assertIsInstance(bid_result, Bid)
        self.assertEqual('rg', Player.query_first(name=bid.player_name).owner_username)
        self.assertEqual(2, User.query_first(username='rg').player_count)
        self.assertTrue(bid.has_bid('sa'))
        self.assertEqual(Bid.NO_BALANCE, [bd['amount'] for bd in bid.bid_map if bd['username'] == 'sa'][0])

        # Bid for next player and check for a tie
        bid = bid_result
        bid_result = accept_bid(bid, User.query_first(username='nz'), 5000)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='pp'), 5000)
        self.assertEqual(Bid.SUCCESS, bid_result)
        bid_result = accept_bid(bid, User.query_first(username='rg'), 5000)
        self.assertEqual(Bid.ERROR_NO_MORE_PLAYERS, bid_result)
        self.assertIn(Player.query_first(name=bid.player_name).owner_username, ['nz', 'pp', 'rg'])
        game.refresh()
        self.assertEqual(0, game.player_to_bid)
        self.assertIsNone(game.player_in_bidding)
        self.assertFalse(game.bid_in_progress)
        self.assertEqual(0, game.user_to_bid)

        # Check bids view
        bids = bids_view()
        self.assertEqual(5, len(bids))
        self.assertEqual('Jasprit Bumrah', bids[0].player_name)
        test_usernames = ['nz', 'pp', 'rg', 'sa']
        db_usernames = [bd['username'] for bd in bids[0].bid_map]
        self.assertListEqual(test_usernames, db_usernames)

        # Check paginated bids view
        page = bids_view(3)
        page = bids_view(page.per_page, end=page.current_end.doc_id)
        self.assertEqual('Rohit Sharma', page.items[0].player_name)
        db_usernames = [bd['username'] for bd in page.items[0].bid_map]
        self.assertListEqual(test_usernames, db_usernames)


class UploadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.upload_data = Upload()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_upload_users(self):
        test_users = {
            'ag': TestConfig.INITIAL_BUDGET,
            'as': TestConfig.INITIAL_BUDGET,
            'fa': TestConfig.INITIAL_BUDGET,
            'mb': TestConfig.INITIAL_BUDGET,
            'nz': TestConfig.INITIAL_BUDGET,
            'pp': TestConfig.INITIAL_BUDGET,
            'rd': TestConfig.INITIAL_BUDGET,
            'sc': TestConfig.INITIAL_BUDGET,
            'vp': TestConfig.INITIAL_BUDGET,
        }
        # Upload
        self.upload_data.file_name = self.app.config.get('USER_FILE_NAME')
        result = self.upload_data('users')
        self.assertEqual(Upload.SUCCESS, result)
        users = User.get_all()
        self.assertEqual(len(test_users), len(users))
        db_users = {}
        for user in users:
            db_users[user.username] = user.balance
        self.assertDictEqual(test_users, db_users)
        # Test fail codes
        upload_data = Upload()
        self.assertEqual(Upload.ERROR_NOT_VALID_TYPE, upload_data())
        self.assertEqual(Upload.ERROR_NOT_VALID_TYPE, upload_data('test'))
        Upload.ACCEPTED_TYPES.append('test')
        self.assertEqual(Upload.ERROR_FILE_NOT_FOUND, upload_data('test'))
        Upload.ACCEPTED_TYPES.pop()

    def test_upload_players(self):
        result = self.upload_data('players')
        self.assertEqual(Upload.SUCCESS, result)
        players = Player.get_all()
        self.assertEqual(150, len(players))
        angelo = Player.query_first(name='Angelo Mathews')
        self.assertEqual(4.1, angelo.overs_per_match)
        self.assertEqual(26.4, angelo.runs_per_match)
        self.assertEqual(0.6, angelo.wickets_per_match)
        # Test pagination
        page = available_players_view(25)
        self.assertEqual(1, page.current_start.bid_order)
        self.assertEqual(25, page.current_end.bid_order)
        self.assertEqual(25, len(page.items))
        self.assertTrue(page.has_next)
        self.assertFalse(page.has_prev)
        page = available_players_view(page.per_page, end=page.current_end.doc_id, direction=FirestorePage.NEXT_PAGE)
        self.assertEqual(26, page.current_start.bid_order)
        self.assertEqual(50, page.current_end.bid_order)
        self.assertEqual(25, len(page.items))
        self.assertTrue(page.has_next)
        self.assertTrue(page.has_prev)
        # Go to the end
        for _ in range(4):
            page = available_players_view(page.per_page, end=page.current_end.doc_id, direction=FirestorePage.NEXT_PAGE)
        self.assertEqual(126, page.current_start.bid_order)
        self.assertEqual(150, page.current_end.bid_order)
        self.assertEqual(25, len(page.items))
        self.assertFalse(page.has_next)
        self.assertTrue(page.has_prev)
        # Test previous page
        page = available_players_view(page.per_page, start=page.current_start.doc_id, direction=FirestorePage.PREV_PAGE)
        self.assertEqual(101, page.current_start.bid_order)
        self.assertEqual(125, page.current_end.bid_order)
        self.assertEqual(25, len(page.items))
        self.assertTrue(page.has_next)
        self.assertTrue(page.has_prev)
        # Go back to the start
        for _ in range(4):
            page = available_players_view(page.per_page, start=page.current_start.doc_id, direction=FirestorePage.PREV_PAGE)
        self.assertEqual(1, page.current_start.bid_order)
        self.assertEqual(25, page.current_end.bid_order)
        self.assertEqual(25, len(page.items))
        self.assertTrue(page.has_next)
        self.assertFalse(page.has_prev)
        # Going beyond start will give you none
        page = available_players_view(page.per_page, start=page.current_start.doc_id, direction=FirestorePage.PREV_PAGE)
        self.assertIsNone(page)

        # Test player stats
        for country in Country.CODES:
            players = Player.query(country_code=country)
            self.assertEqual(15, len(players))
            for player in players:
                # self.assertIsNotNone(player.image_file, f'{player.name}')
                if player.wickets > 0:
                    if 'spin bowler' not in player.tags and 'fast bowler' not in player.tags:
                        self.assertFalse(True, f'No bowler tag for player who has taken wickets for {player.name}')
                else:
                    if 'spin bowler' in player.tags or 'fast bowler' in player.tags:
                        self.assertFalse(True, f'Bowler tag exists for player who has not taken wickets for {player.name}')

        # Test search tags
        tags = (country.lower(), '-backup')
        players = search_players_view(tags)['players']
        self.assertEqual(11, len(players), f'{tags}')
        tags = ('captain', country.lower())
        players = search_players_view(tags)['players']
        self.assertEqual(1, len(players), f'{tags}')
        tags = ('-sl', '-wi', '-afg', '-aus', '-nz', '-sa', '-eng', '-ban')
        players = search_players_view(tags)['players']
        self.assertEqual(30, len(players), f'{tags}')

    def test_upload_scores(self):
        result = self.upload_data('scores')
        self.assertEqual(Upload.SUCCESS, result, result)

    def test_country(self):
        aus = Country('Aus')
        self.assertEqual('Australia', aus.name)
        ind = Country('INDIA')
        self.assertEqual(2, ind.rank)
        sa = Country('south africa')
        self.assertEqual('forestgreen', sa.bg_color)
        self.assertEqual('yellow', sa.color)

    def test_upload_all(self):
        result = Upload.upload_all()
        self.assertEqual(Upload.SUCCESS, result)


class AutoBidTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.upload_data = Upload()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_auto_bid(self):
        users = User.get_all()
        self.assertEqual(9, len(users))
        game = Game.read()
        self.assertIsNotNone(game)
        self.assertEqual(9, game.user_count)
        self.assertEqual(150, game.player_count)
        self.assertEqual(150, game.player_to_bid)
        self.assertFalse(game.bid_in_progress)
        invite_bid()
        game.refresh()
        while game.bid_in_progress:
            bid = Bid.query_first(player_name=game.player_in_bidding)
            for user in users:
                user.refresh()
                if user.balance > 0:
                    sbp = game.avg_player_bid
                    amount = randrange(sbp - 20, sbp + 20)
                    if user.balance < amount:
                        amount = user.balance
                    accept_bid(bid, user, amount)
            game.refresh()
        self.assertEqual(0, game.player_to_bid)


class DownloadTest(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.upload_data = Upload()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_download(self):
        download_data = Download()
        download_data()
        self.assertTrue(os.path.isfile(download_data.file_name))

