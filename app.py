from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'supersecretkey')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pmai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ------------------------- Models ------------------------- #
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    joined = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    mode = db.Column(db.String(50))
    lang = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ------------------------- Routes ------------------------- #

@app.route('/')
def home():
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if not all([username, email, password, confirm]):
            flash("Please fill all fields.")
            return redirect(url_for('register'))
        if password != confirm:
            flash("Passwords do not match.")
            return redirect(url_for('register'))
        if len(password) < 6:
            flash("Password must be at least 6 characters long.")
            return redirect(url_for('register'))

        hashed_pw = generate_password_hash(password)
        user = User(username=username, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('chat'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('chat'))
        else:
            flash("Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out.")
    return redirect(url_for('home'))

@app.route('/chat')
@login_required
def chat():
    messages = Message.query.filter_by(user_id=current_user.id).all()
    return render_template('chat.html', messages=messages, user=current_user)

@app.route('/send', methods=['POST'])
@login_required
def send():
    data = request.get_json()
    msg = data.get('message')
    mode = data.get('mode', 'Chatbox')
    lang = data.get('lang', 'English')

    # Simulated response
    reply = f"[{mode}] ({lang}) Response to: {msg}"

    message = Message(user_id=current_user.id, prompt=msg, response=reply, mode=mode, lang=lang)
    db.session.add(message)
    db.session.commit()

    return jsonify({'reply': reply})

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/admin')
@login_required
def admin():
    if current_user.email != "magamiabu@gmail.com":
        flash("Unauthorized access.")
        return redirect(url_for('chat'))

    users = User.query.all()
    messages = Message.query.order_by(Message.timestamp.desc()).limit(50).all()

    # Mode usage stats
    mode_counts = {}
    for msg in messages:
        mode_counts[msg.mode] = mode_counts.get(msg.mode, 0) + 1

    return render_template('admin.html',
                           total_users=len(users),
                           emails=[u.email for u in users],
                           messages=[{
                               'prompt': m.prompt,
                               'response': m.response,
                               'timestamp': m.timestamp.strftime("%Y-%m-%d %H:%M"),
                               'mode': m.mode,
                               'lang': m.lang
                           } for m in messages],
                           mode_counts=mode_counts)

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

# ------------------------- Main ------------------------- #
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
