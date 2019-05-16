import click
from app.main.game_transactions import Upload, invite_bid
from app.models import Game


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
        if not upload_type or not isinstance(upload_type, str):
            raise RuntimeError('Requires one parameter as a upload type.')

        if upload_type not in Upload.ACCEPTED_TYPES:
            raise RuntimeError('Upload of only certain types are accepted. users, players, scores are valid options.')

        upload_data = Upload()
        result = upload_data(upload_type)
        if result != Upload.SUCCESS:
            raise RuntimeError('Some error in upload.')
        if Upload.INIT_GAME[upload_type]:
            Game.init_game()

    @wc.command()
    def bid():
        """ Invite players for bid. """
        game = Game.read()
        if game is None:
            game = Game.init_game()
        if game.bid_in_progress:
            raise RuntimeError('Bid is already in progress.')
        invite_bid()
