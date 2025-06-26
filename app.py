from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime
import requests
import uuid
import os

# === CONFIGURATION ===
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "supersecret")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pmai.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# === DATABASE MODELS ===
class User(db.Model):
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    joined = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(100), db.ForeignKey('user.id'))
    mode = db.Column(db.String(50))
    lang = db.Column(db.String(20))
    prompt = db.Column(db.Text)
    response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# === ROUTES (EXAMPLES) ===
@app.route('/')
def welcome():
    return render_template('welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        if password != confirm:
            return render_template('register.html', error="Passwords do not match.")
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        session['user'] = email
        return redirect(url_for('chat'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session['user'] = email
            return redirect(url_for('chat'))
        return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
