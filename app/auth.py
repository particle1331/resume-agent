from flask import Blueprint, request, redirect, url_for, render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from .database import Database

auth_bp = Blueprint('auth', __name__)
login_manager = LoginManager()

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['user_id']
        self.email = user_data['email']
        self.tokens = user_data.get('tokens', 100)

@login_manager.user_loader
def load_user(user_id):
    db = Database()
    user_data = db.query("SELECT * FROM users WHERE user_id = %s", [user_id])
    return User(user_data[0]) if user_data else None

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = Database()
        user = db.query("SELECT * FROM users WHERE email = %s", [email])
        
        print(password)
        print(user[0]['password'] if user else 'No user found')

        if user and check_password_hash(user[0]['password'], password):
            login_user(User(user[0]))
            return redirect(url_for('resume'))
            
        return "Invalid credentials", 401
        
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
