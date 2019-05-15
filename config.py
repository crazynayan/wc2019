def get_secret_key():
    try:
        with open('secret-key.txt') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


class Config:
    SECRET_KEY = get_secret_key() or 'Some secret key.'
    GAC_KEY_PATH = 'firestore-key.json'
    INITIAL_BUDGET = 10000
    PER_PAGE = 20

