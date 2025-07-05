from flask import Flask, render_template, redirect, url_for, request, session, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from supabase import create_client
import os

# === Supabase Setup ===
SUPABASE_URL = "https://cefiqcndxqdhziwvppkd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNlZmlxY25keHFkaHppd3ZwcGtkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE1NjcwODQsImV4cCI6MjA2NzE0MzA4NH0.VFbFVr3Co7SuVIwkNCwb64x2SdjzbkGjqTiMrTfl8kU"  # Your real anon key here
SUPABASE_BUCKET = "avatars"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Flask Setup ===
app = Flask(__name__)
app.secret_key = 'secret123'
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# === Routes ===
@app.route('/')
def index():
    if 'user_id' in session:
        user_data = supabase.table('users').select("*").eq('id', session['user_id']).execute()
        user = user_data.data[0] if user_data.data else None
        if user:
            birthdays_data = supabase.table('birthdays').select("*").eq('user_id', user['id']).execute()
            birthdays = birthdays_data.data if birthdays_data.data else []
            return render_template('birthdays.html', birthdays=birthdays, username=user['username'], user=user)
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
        existing = supabase.table('users').select("*").eq('username', username).execute()
        if existing.data:
            flash("Username already taken!", "error")
            return redirect('/register')
        result = supabase.table('users').insert({
            'username': username,
            'password': password,
            'profile_pic': ''
        }).execute()
        flash("Registration successful! Please log in.", "success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        result = supabase.table('users').select("*").eq('username', username).execute()
        user = result.data[0] if result.data else None
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
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
    date = request.form['date']
    supabase.table('birthdays').insert({
        'name': name,
        'date': date,
        'user_id': session['user_id']
    }).execute()
    flash("Birthday added!", "success")
    return redirect('/')

@app.route('/delete/<string:id>')
def delete(id):
    if 'user_id' not in session:
        return redirect('/login')
    b = supabase.table('birthdays').select("*").eq('id', id).execute().data
    if b and b[0]['user_id'] == session['user_id']:
        supabase.table('birthdays').delete().eq('id', id).execute()
        flash("Birthday deleted!", "info")
    return redirect('/')

@app.route('/upload_profile', methods=['POST'])
def upload_profile():
    if 'user_id' not in session:
        return redirect('/login')
    file = request.files['profile']
    if file:
        filename = secure_filename(file.filename)
        path = f"{session['user_id']}/{filename}"
        supabase.storage.from_(SUPABASE_BUCKET).upload(path, file, {"upsert": True})
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{path}"
        supabase.table('users').update({'profile_pic': public_url}).eq('id', session['user_id']).execute()
        flash("Profile picture updated!", "success")
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
