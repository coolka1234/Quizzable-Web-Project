from dotenv import load_dotenv
import os
from flask import Flask, redirect, url_for, session, render_template, g, request
from flask_dance.contrib.google import make_google_blueprint, google
from flask_sqlalchemy import SQLAlchemy

load_dotenv()

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

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)

with app.app_context():
    db.create_all()

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
    return render_template("index.html", name=g.user.name, email=g.user.email)

@app.route('/new_quiz', methods=['GET', 'POST'])
def new_quiz():
    if request.method == 'POST':
        pass
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
    app.run(debug=True, ssl_context='adhoc')
