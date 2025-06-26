#<!-- Continued: Flask backend and integration (app.py) -->
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import requests
import os
import cohere
import flask
from flask import request, jsonify

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pmai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# COHERE & IPQS SETUP
co = cohere.Client("YOUR_COHERE_API_KEY")
ipqs_api_key = "YOUR_IPQS_API_KEY"
admin_email = "magamiabu@gmail.com"

# ===================== MODELS =====================
class User(db.Model):
    id = db.Column(db.String, primary_key=True)
    username = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    joined = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False)

class Message(db.Model):
    id = db.Column(db.String, primary_key=True)
    user_id = db.Column(db.String)
    mode = db.Column(db.String(50))
    lang = db.Column(db.String(20))
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ===================== ROUTES =====================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if len(password) < 8 or password != confirm:
            return render_template('register.html', error="Passwords must match and be 8+ characters")

        existing = User.query.filter_by(email=email).first()
        if existing:
            return render_template('register.html', error="Email already registered")

        new_user = User(id=str(uuid.uuid4()), username=username, email=email, password=password,
                        is_admin=(email == admin_email))
        db.session.add(new_user)
        db.session.commit()
        session['user_id'] = new_user.id
        return redirect(url_for('chat'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            return redirect(url_for('chat'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/chat')
def chat():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html')

@app.route('/api/message', methods=['POST'])
def handle_message():
    data = request.get_json()
    user_id = session.get('user_id', 'guest')
    prompt = data.get('prompt')
    lang = data.get('lang')
    mode = data.get('mode')

    # Scam check
    if mode == "Scam/Email Checker":
        check_url = f"https://ipqualityscore.com/api/json/url/{ipqs_api_key}/{prompt}"
        res = requests.get(check_url).json()
        result = res.get("domain", "") + (" is dangerous." if res.get("unsafe") else " is safe.")
    else:
        if lang == "Pidgin":
            prompt = f"Explain in Nigerian pidgin: {prompt}"
        co_response = co.generate(model="command-r-plus", prompt=prompt, max_tokens=200)
        result = co_response.generations[0].text.strip()

    # Save if logged in
    if user_id != 'guest':
        msg = Message(id=str(uuid.uuid4()), user_id=user_id, mode=mode, lang=lang, prompt=prompt, response=result)
        db.session.add(msg)
        db.session.commit()

    return jsonify({"reply": result})

@app.route('/api/history')
def chat_history():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([])
    msgs = Message.query.filter_by(user_id=user_id).order_by(Message.timestamp.desc()).limit(50).all()
    return jsonify([{ "prompt": m.prompt, "response": m.response, "mode": m.mode, "lang": m.lang } for m in msgs])

@app.route('/admin')
def admin():
    uid = session.get('user_id')
    user = User.query.filter_by(id=uid).first()
    if not user or not user.is_admin:
        return redirect(url_for('chat'))
    users = User.query.all()
    messages = Message.query.all()
    return render_template("admin.html", users=users, messages=messages)
@app.route("/send", methods=["POST"])
def send():
    if request.method == "POST":
        data = request.get_json()
        message = data.get("message")
        mode = data.get("mode")
        lang = data.get("lang")

        if not message:
            return jsonify({"reply": "Please enter a valid message."})

        prompt = message
        if mode == "Scam/Email Checker":
            reply = scam_check(prompt)
        else:
            if lang == "Pidgin":
                prompt = f"Explain in Nigerian pidgin: {prompt}"
            reply = get_response(prompt)

        # Save message if logged in
        if "user" in session and session["user"]:
            user = session["user"]
            save_message(user["id"], mode, lang, message, reply)

        return jsonify({"reply": reply})

# ===================== RUN =====================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
