from dotenv import load_dotenv
import os
from flask import Flask, redirect, url_for, session, render_template, g, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_dance.contrib.google import make_google_blueprint, google
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from flask_migrate import Migrate
from functions import generate_game_code

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")




GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

google_bp = make_google_blueprint(
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    redirect_to="google_callback",
    scope=["https://www.googleapis.com/auth/userinfo.email", "openid", "https://www.googleapis.com/auth/userinfo.profile"],
)
app.register_blueprint(google_bp, url_prefix="/login")

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)

class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    user = db.relationship('User', backref='quizzes')

    questions = db.relationship('Question', backref='quiz', cascade="all, delete-orphan", lazy=True)


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)

    answers = db.relationship('Answer', backref='question', cascade="all, delete-orphan", lazy=True)


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300), nullable=False)
    label = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)

with app.app_context():
    db.create_all()

migrate = Migrate(app, db)

@app.before_request
def before_request():
    g.logged_in = google.authorized
    if g.logged_in:
        resp = google.get("/oauth2/v1/userinfo")
        if resp.ok:
            user_info = resp.json()
            name = user_info.get("name")
            email = user_info.get("email")
            session['name'] = name
            session['email'] = email

            user = User.query.filter_by(email=email).first()
            if not user:
                user = User(
                    name=name,
                    email=email
                )
                db.session.add(user)
                db.session.commit()
            g.user = user
        else:
            session.pop('name', None)
            session.pop('email', None)
            g.user = None
    else:
        session.pop('name', None)
        session.pop('email', None)
        g.user = None

@app.route("/")
def login_page():
    if g.logged_in:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/index")
def index():
    if not g.logged_in:
        return redirect(url_for("login_page"))
    
    quizzes = Quiz.query.all()
    return render_template("index.html", quizzes=quizzes)

@app.route('/create')
def create(quiz_id=None):
    code = generate_game_code()
    quiz = Quiz.query.get(quiz_id) if quiz_id else None
    if quiz:
        questions = quiz.questions
        answers = {question.id: question.answers for question in questions}
    else:
        questions = []
        answers = {}
    return render_template('lobby.html', game_code=code, questions=questions, answers=answers)


@app.route('/join/<code>')
def join(code):
    return render_template('lobby.html', game_code=code)

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
    sid = request.sid
    # TODO: tu musi być logika sprawdzajaca odpowiedź

@socketio.on('disconnect')
def on_disconnect():
    return
    if request.sid in games[code]['players']:
        leave_room(code)
        del games[code]['players'][request.sid]

@app.route('/new_quiz', methods=['GET', 'POST'])
def new_quiz():
    if request.method == 'POST':
        print(request.form)
        name = request.form.get("name")
        category = request.form.get("category")

        new_quiz = Quiz(name=name, category=category, user_id=g.user.id, created_at=datetime.now(timezone.utc))
        db.session.add(new_quiz)
        db.session.flush()

        index = 0
        while True:
            question_text = request.form.get(f"question_{index}")
            if not question_text:
                break

            question = Question(text=question_text, quiz_id=new_quiz.id)
            db.session.add(question)
            db.session.flush()

            correct_answer = request.form.get(f"correct_answer_{index}")

            for i in range(1, 5):
                answer_text = request.form.get(f"answer_{index}_{i}")
                if not answer_text:
                    continue

                label = chr(64 + i)
                is_correct = str(i) == correct_answer

                answer = Answer(
                    text=answer_text,
                    label=label,
                    is_correct=is_correct,
                    question_id=question.id
                )
                db.session.add(answer)

            index += 1
        print("Dodano pytania i odpowiedzi do bazy danych")
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('new_quiz.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route("/login/google/callback")
def google_callback():
    if not google.authorized:
        return "Nie udało się zalogować przez Google.", 400
    return redirect(url_for("index"))

if __name__ == "__main__":
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, ssl_context='adhoc')
