import csv
import click
from app.main.game_transactions import upload_users


def register(app):
    @app.cli.group()
    def wc():
        """World Cup commands."""
        pass

    @wc.command()
    @click.argument('file_name')
    def upload(file_name):
        """
        Upload data.
        Takes one parameter as file_name which should be a csv file.
        users.csv - 'username', 'name', 'password', 'color', 'bg_color'.
        players.csv - To be developed
        """
        if not file_name or not isinstance(file_name, str) or file_name[-4:] != '.csv':
            raise RuntimeError('Requires one parameter as file name which should be a .csv file.')

        accepted_files = ['users.csv', 'players.csv']

        if file_name not in accepted_files:
            raise RuntimeError('Upload of only certain files are accepted. users.csv and players.csv')

        if file_name == 'users.csv':
            try:
                with open(file_name) as csv_file:
                    user_list = list(csv.reader(csv_file))
            except FileNotFoundError:
                raise RuntimeError('File users.csv not found.')
            if user_list[0] != ['username', 'name', 'password', 'color', 'bg_color']:
                raise RuntimeError('users.csv is not in the proper format')
            upload_users(user_list[1:])


