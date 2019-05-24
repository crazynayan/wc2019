import os
import click
from app.main.game_transactions import Upload, invite_bid
from app.models import Game
from config import TestConfig


def register(app):
    @app.cli.group()
    def wc():
        """World Cup commands."""
        pass

    @wc.command()
    @click.argument('upload_type')
    def upload(upload_type):
        """
        Upload data.
        UPLOAD_TYPE can be [users | players | scores]\n
        File name as <UPLOAD_TYPE>.csv should exists in the current project folder.\n
        users.csv - 'username', 'name', 'password', 'color', 'bg_color'.\n
        players.csv - 'name', 'country', 'type', 'tags', 'matches', 'runs', 'wickets', 'balls', 'bid_order'\n
        scores.csv - To be developed\n
        """
        if os.environ.get('WC_ENVIRONMENT') == 'dev':
            click.echo('You are running this command on DEV server')
        else:
            click.echo('You are running this command on the PROD sever.')

        if upload_type not in Upload.ACCEPTED_TYPES:
            click.echo('Upload of only certain types are accepted. users, players, scores are valid options.')
            return

        upload_data = Upload()
        if os.environ.get('WC_ENVIRONMENT') == 'dev' and upload_type == 'users':
            upload_data.file_name = TestConfig.USER_FILE_NAME
        result = upload_data(upload_type)
        if result != Upload.SUCCESS:
            click.echo(f'Error Code: {result}. Error in upload.')
            return
        click.echo('Upload done!')

    @wc.command()
    @click.argument('command')
    def bid(command):
        """
        Control bid status.\n
        start - Start players for bid.\n
        pause - Pause bidding.\n
        resume - Resume bidding.\n
        """
        if os.environ.get('WC_ENVIRONMENT') == 'dev':
            click.echo('You are running this command on DEV server')
        else:
            click.echo('You are running this command on the PROD sever.')

        game = Game.read()
        if game is None:
            game = Game.init_game()

        command = command.lower().strip()

        if command not in ['start', 'pause', 'resume']:
            click.echo('Valid options are start, pause or resume.')
            return

        if game.user_count == 0 or game.player_count == 0:
            click.echo('Init the game first by uploading player data.')
            return

        if game.player_to_bid == 0:
            click.echo('Bidding is complete')
            return

        if command == 'start':
            if game.bid_in_progress:
                click.echo('Bid is already in progress.')
                return
            if game.player_to_bid != game.player_count:
                click.echo('Bidding has already started. Use resume option.')
                return
            invite_bid()
            click.echo('Bidding has been started.')
            return

        if command == 'pause':
            if not game.bid_in_progress:
                click.echo('Bid is NOT in progress.')
                return
            game.bid_in_progress = False
            game.update()
            click.echo('Bidding has been paused.')
            return

        if command == 'resume':
            if game.bid_in_progress:
                click.echo('Bid is already in progress.')
                return
            if game.player_to_bid == game.player_count:
                click.echo('Bidding has not yet started. Use start option.')
                return
            game.bid_in_progress = True
            game.update()
            click.echo('Bidding has been resumed.')


