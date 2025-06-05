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
        emit("player_joined", {"name": name}, room=code) # type: ignore


    @socketio.on('start_game')
    def start_game(data):
        code = data['game_code']
        id = data['quiz_id']
        print(f"Starting game {code} for quiz {id}")
        emit('game_started', {'quiz_id': id}, room=code) # type: ignore
    
    @socketio.on('start_game_host')
    def start_game_host(data):
        code = data['game_code']
        id = data['quiz_id']
        print(f"Host starting game {code} for quiz {id}")
        emit('game_started_host', {'quiz_id': id}, room=code) # type: ignore
        
    @socketio.on('submit_player_answer')
    def handle_player_answer(data):
        name = data['player_name']
        game_code = data['game_code']
        question_index = data['question_index']
        total_questions = data['total_questions']
        is_correct = data['is_correct']
        answer_time = data['time']
        
        print(f"Player {name} answered question {question_index}/{total_questions} in {answer_time}s")
        
        emit('player_answer', {
            'name': name,
            'questionIndex': question_index,
            'totalQuestions': total_questions,
            'correct': is_correct,
            'time': answer_time
        }, room=game_code) # type: ignore
        
        if int(question_index) + 1 >= int(total_questions):
            print(f"Player {name} completed the quiz")
            emit('player_completed', {'name': name}, room=game_code) # type: ignore
            
    @socketio.on('all_players_completed')
    def handle_quiz_completed(data):
        game_code = data['game_code']
        quiz_id = data['quiz_id']
        
        print(f"All players completed quiz {quiz_id} in game {game_code}")
        
        emit('quiz_completed', {'quiz_id': quiz_id}, room=game_code) # type: ignore

