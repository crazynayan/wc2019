import csv
from app.main.game_transactions import upload_users


def register(app):
    @app.cli.group()
    def upload():
        """Upload commands."""
        pass

    @upload.command()
    def users():
        """
        Upload users.
        Need users.csv in the project folder.
        Format of the users.csv should be as follows:
        username, name, password, color, bg_color
        """
        try:
            with open('users.csv') as csv_file:
                user_list = list(csv.reader(csv_file))
        except FileNotFoundError:
            raise RuntimeError('File users.csv not found.')

        if user_list[0] != ['username', 'name', 'password', 'color', 'bg_color']:
            raise RuntimeError('users.csv is not in the proper format')

        upload_users(user_list[1:])


