from flask import request
from flask_socketio import emit, join_room
from flask_socketio import SocketIO, join_room, leave_room

def register_socketio_events(socketio):

    @socketio.on("join_game")
    def handle_join_game(data):
        name = data["name"]
        code = data["game_code"]
        join_room(code)
        print(f"Player {name} joined game {code}")
        emit("player_joined", {"name": name}, room=code)


    @socketio.on('start_game')
    def start_game(data):
        code = data['game_code']
        id = data['quiz_id']
        emit('game_started', {'quiz_id': id}, room=code)

