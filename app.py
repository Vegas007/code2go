import sqlalchemy
from flask import Flask, url_for, request, redirect, render_template
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
from utils import *
import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt


# Auth Grade Enum
class AuthGrade(Enum):
    NONE = 0
    STUDENT = 1
    INSTRUCTOR = 2
    ADMIN = 3


# Debug mode
DEBUG = True

# App configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.jinja_env.auto_reload = True

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Crypt initialization
bcrypt = Bcrypt(app)

# Database initialization
db = SQLAlchemy(app)
db.init_app(app)


##################################
# Database schema
##################################
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(128), nullable=False)
    date_joined = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    auth_grade = db.Column(db.Integer, nullable=False, default=AuthGrade.STUDENT)

    def __repr__(self):
        return f'''
            id: {self.id}
            full_name: {self.full_name}
            password: {self.password}
            email: {self.email}
            date_joined: {self.date_joined}
            auth_grade: {self.auth_grade}
        '''


class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    instructor_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(512), nullable=False)
    video_url = db.Column(db.String(128), nullable=False)
    category = db.Column(db.String(32), nullable=False)
    sub_category = db.Column(db.String(32), nullable=False)
    last_updated = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False, default=0.0)

    def __repr__(self):
        return f'''
            id: {self.id}
            instructor_id: {self.instructor_id}
            title: {self.title}
            description: {self.description}
            video_url: {self.video_url}
            category: {self.category}
            sub_category: {self.sub_category}
            last_updated: {self.last_updated}
            price: {self.price}
        '''


##################################
# General functions
##################################
@login_manager.user_loader
def load_user(user_id):
    """
    :param user_id: int
    :return: int
    """
    return User.query.get(int(user_id))


def is_logged():
    """
    :return: bool
    """
    return current_user and current_user.is_authenticated


def get_auth_grade(email):
    """
    :rtype: int
    :param email: string
    """
    user = User.query.filter_by(email=email).first()
    if user:
        return user.auth_grade
    return 0


def validate_email(email):
    """
    :param username: string
    """
    existing_user_username = User.query.filter_by(email=email).first()
    if existing_user_username:
        return False
    return True


def get_courses_by_id(id):
    """
    :param id: int
    :return: List[Dict]
    """
    if user:
        courses = Course.query.filter_by(instructor_id=id).all()
        return courses
    return None


def get_all_courses():
    """
    :return: List[Dict]
    """
    courses = Course.query.all()
    return courses


##################################
# Routes
##################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    print(request.values)

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            print(f"Login succeded!\n{user}")
            # user.authenticated = True
            login_user(user)
            return redirect(url_for('home'))
        else:
            print("Login failed!")

    return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    return render_template('create.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    print(request.values)

    content = {
        'auth_grade': {i.name: i.value for i in AuthGrade},
        'output_message': '',
    }

    if request.method == 'POST':
        full_name = request.form['full_name']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        email = request.form['email']
        auth_grade = int(request.form['checkbox_auth'])

        if not validate_email(email):
            content['output_message'] = 'This email already exists. Please choose a different one.'
            return render_template('register.html', content=content)

        user = User(full_name=full_name, password=password, email=email, auth_grade=auth_grade)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('login'))
        except BaseException as f:
            content['output_message'] = f'There was an issue with registration. {f}'
            return render_template('register.html', content=content)

    return render_template('register.html', content=content)


@app.route('/')
def home():
    if is_logged():
        # TODO: Send my own courses
        # params = {
        #     'all_courses': get_all_courses(),
        #     'own_courses': get_courses_by_id(current_user.id),
        # }
        return render_template('dashboard.html', courses=get_all_courses())
    else:
        return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=DEBUG)

with app.app_context():
    db.create_all()
