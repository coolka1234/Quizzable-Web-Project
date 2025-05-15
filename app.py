from dotenv import load_dotenv
import os
from flask import Flask, redirect, url_for, session, render_template
from flask_dance.contrib.google import make_google_blueprint, google

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

@app.route("/")
def index():
    if google.authorized:
        resp = google.get("/oauth2/v1/userinfo")
        assert resp.ok, resp.text
        user_info = resp.json()
        session['name'] = user_info.get("name")
        session['email'] = user_info.get("email")
        return render_template('index.html', logged_in=True, name=session.get('name'), email=session.get('email'))
    return render_template('index.html', logged_in=False)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/login/google/callback")
def google_callback():
    resp = google.authorized
    if not resp:
        return "Nie udało się zalogować przez Google.", 400
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, ssl_context='adhoc')
