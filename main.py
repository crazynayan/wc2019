import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import config
from firestore_model import init_firestore_db
from app.models import Player, Game
from app.main.game_transactions import sync_player_user_points


def update_scores(data, context):
    # Use creds to create a client to interact with the Google Drive API
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']

    creds = ServiceAccountCredentials.from_json_keyfile_name(config.GAC_KEY_PATH, scope)
    client = gspread.authorize(creds)

    # Open the work book
    sheet = client.open("wc2019").worksheet("scores")
    players_dict = sheet.get_all_records()

    # Init database
    init_firestore_db(config.GAC_KEY_PATH)

    # Check if update required
    game = Game.read()
    if not game:
        return False
    try:
        total_score = sum([float(player['score']) for player in players_dict])
    except ValueError:
        total_score = 0
    if total_score != 0 and game.total_score == total_score:
        return False

    # Update player score
    players = Player.get_all()
    Player.init_batch()
    for player in players:
        player_item = next((item for item in players_dict if item['player'] == player.name), None)
        if not player_item:
            continue
        try:
            player.score = round(float(player_item['score']), 1)
            player.update_batch()
        except ValueError:
            continue
    Player.commit_batch()
    sync_player_user_points()
    game.total_score = total_score
    game.update()
    return True

