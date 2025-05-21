import random, string

def generate_game_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))