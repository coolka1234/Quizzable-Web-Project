from flask import Flask, g, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_dance.contrib.google import make_google_blueprint, google
from dotenv import load_dotenv
from flask_migrate import Migrate
import os

load_dotenv()
db = SQLAlchemy()
migrate = Migrate()

socketio = SocketIO(async_mode='threading', cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.secret_key = os.urandom(24)


    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

    google_bp = make_google_blueprint(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_to="google_callback",
        scope=["https://www.googleapis.com/auth/userinfo.email", "openid", "https://www.googleapis.com/auth/userinfo.profile"],
    )
    app.register_blueprint(google_bp, url_prefix="/login")

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    from app.models import User, Quiz, Question

    db.init_app(app)
    socketio.init_app(app)

    with app.app_context():
        db.create_all()  
        print("Database tables created")

    migrate = Migrate(app, db)  

    from .routes import register_routes
    from .socketio_events import register_socketio_events
    register_routes(app, google, session, g)
    register_socketio_events(socketio)

    return app
