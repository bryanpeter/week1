from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///week1.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

db = SQLAlchemy(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    birthday = db.Column(db.String(10), nullable=False)  
    address = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_image = db.Column(db.String(120), nullable=True)
    
@app.route('/')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to access this page.", "error")
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        birthday = request.form['birthday']
        address = request.form['address']
        username = request.form['username']
        password = request.form['password']

        if 'profile_image' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        profile_image = request.files['profile_image']

        if profile_image and allowed_file(profile_image.filename):
            filename = secure_filename(profile_image.filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            profile_image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            image_path = f"uploads/{filename}"  # Save path relative to /static

            hashed_password = generate_password_hash(password)
            new_user = User(
                name=name,
                birthday=birthday,
                address=address,
                username=username,
                password=hashed_password,
                profile_image=image_path
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', "success")
            return redirect(url_for('login'))
        else:
            flash('Invalid image format. Please upload a valid image.', "error")
            return redirect(request.url)

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username_email']
        password = request.form['password']

        user = User.query.filter((User .username == username)).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', "success")
            return redirect(url_for('result'))
        else:
            flash('Invalid credentials. Please try again.', "error")

    return render_template('login.html')

@app.route('/result')
def result():
    if 'user_id' not in session:
        flash("Please log in to view your info.", "error")
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    # Convert birthday string to date and calculate age
    try:
        birthdate = datetime.strptime(user.birthday, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
    except ValueError:
        age = "Unknown"

    return render_template('result.html', user=user, age=age)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create database tables
    app.run(debug=True)
