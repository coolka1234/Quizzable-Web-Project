from flask_sqlalchemy import SQLAlchemy
from . import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    results = db.relationship('Result', backref='user', cascade="all, delete-orphan")
    answers = db.relationship('UserAnswer', backref='user', cascade="all, delete-orphan")
    quizzes = db.relationship('Quiz', backref='user', cascade="all, delete-orphan")


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)

    questions = db.relationship('Question', backref='quiz', cascade="all, delete-orphan", lazy=True)
    results = db.relationship('Result', backref='quiz', cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)

    answers = db.relationship('Answer', backref='question', cascade="all, delete-orphan", lazy=True)
    user_answers = db.relationship('UserAnswer', backref='question', cascade="all, delete-orphan")


class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(300), nullable=False)
    label = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, default=False)

    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_answers = db.relationship('UserAnswer', backref='answer', cascade="all, delete-orphan")


class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)


class UserAnswer(db.Model):
    __tablename__ = 'user_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    answer_id = db.Column(db.Integer, db.ForeignKey('answers.id'), nullable=False)
    game_code = db.Column(db.String(10), nullable=False)

