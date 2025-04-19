from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import db, User, Thought, init_db
import os
from datetime import datetime, timedelta ,date


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///daily_thoughts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
init_db(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Delete old thoughts (run this before each request)
@app.before_request
def delete_old_thoughts():
    # Delete thoughts that are not from today
    old_thoughts = Thought.query.filter(Thought.created_at < datetime.combine(date.today(), datetime.min.time()))
    for thought in old_thoughts:
        db.session.delete(thought)
    db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            flash('Username already taken', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return redirect(url_for('register'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/thoughts', methods=['GET', 'POST'])
@login_required
def thoughts():
    if request.method == 'POST':
        content = request.form['content']
        if content:
            new_thought = Thought(content=content, user_id=current_user.id)
            db.session.add(new_thought)
            db.session.commit()
            flash('Your thought has been shared!', 'success')
    
    # Get today's thoughts ordered by creation time (newest first)
    today_thoughts = Thought.query.filter(
        Thought.created_at >= datetime.combine(date.today(), datetime.min.time())
    ).order_by(Thought.created_at.desc()).all()
    
    return render_template('thoughts.html', thoughts=today_thoughts)

@app.route('/delete_thought/<int:thought_id>', methods=['POST'])
@login_required
def delete_thought(thought_id):
    thought = Thought.query.get_or_404(thought_id)
    if thought.user_id == current_user.id:
        db.session.delete(thought)
        db.session.commit()
        flash('Your thought has been deleted.', 'success')
    else:
        flash('You can only delete your own thoughts.', 'error')
    return redirect(url_for('thoughts'))

@app.route('/users')
@login_required
def users():
    all_users = User.query.order_by(User.username).all()
    return render_template('users.html', users=all_users)

@app.route('/write-thought')
@login_required
def write_thought():
    return render_template('write_thought.html')
 
@app.route('/submit-thought', methods=['POST'])
@login_required
def submit_thought():
    content = request.form['content']
    if content:
        new_thought = Thought(content=content, user_id=current_user.id)
        db.session.add(new_thought)
        db.session.commit()
        flash('Your thought has been shared!', 'success')
    return redirect(url_for('thoughts'))


if __name__ == '__main__':
    app.run(debug=True)