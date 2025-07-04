from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from supabase import create_client

SUPABASE_URL = "https://cefiqcndxqdhziwvppkd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # your full key
SUPABASE_BUCKET = "avatars"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.secret_key = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.db')
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Initialize DB
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profile_pic = db.Column(db.String(300), default='')
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(200))
    birthdays = db.relationship('Birthday', backref='user')

class Birthday(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            birthdays = user.birthdays
            return render_template('birthdays.html', birthdays=birthdays, username=user.username, user=user)
        session.pop('user_id', None)
    return redirect('/home')

@app.route('/home')
def home():
    if 'user_id' in session:
        return redirect('/')
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "error")
            return redirect('/register')
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash("Registration successful! Please log in.", "success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash("Login successful!", "success")
            return redirect('/')
        flash("Invalid credentials!", "error")
        return redirect('/login')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("Logged out successfully.", "info")
    return redirect('/login')

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')
    name = request.form['name']
    date = datetime.strptime(request.form['date'], '%Y-%m-%d')
    b = Birthday(name=name, date=date, user_id=session['user_id'])
    db.session.add(b)
    db.session.commit()
    flash("Birthday added!", "success")
    return redirect('/')

@app.route('/delete/<int:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')
    b = Birthday.query.get(id)
    if b and b.user_id == session['user_id']:
        db.session.delete(b)
        db.session.commit()
        flash("Birthday deleted!", "info")
    return redirect('/')

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'user_id' not in session:
        return redirect('/login')
    file = request.files['profile']
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        user = User.query.get(session['user_id'])
        user.profile_pic = f'uploads/{filename}'
        db.session.commit()
        flash("Profile picture updated!", "success")
    return redirect('/')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
