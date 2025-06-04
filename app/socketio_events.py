from flask import request
from flask_socketio import emit, join_room
from flask_socketio import SocketIO, join_room, leave_room

def register_socketio_events(socketio):

    @socketio.on('join_game')
    def on_join(data):
        name = data['name']
        code = data['game_code']
        join_room(code)
        emit('player_joined', {'name': name}, room=code)

    @socketio.on('start_game')
    def start_game(data):
        code = data['game_code']
        emit('next_question', {'q': "Sample Question?"}, room=code)

    @socketio.on('submit_answer')
    def answer(data):
        code = data['game_code']
        # sid = request.sid
        # TODO: tu musi być logika sprawdzajaca odpowiedź

    @socketio.on('disconnect')
    def on_disconnect():
        return
        if request.sid in games[code]['players']:
            leave_room(code)
            del games[code]['players'][request.sid]
