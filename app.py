from flask import Flask, flash, url_for, request, redirect, render_template
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from flask_bcrypt import Bcrypt
from flask import send_from_directory

from wtforms import StringField, SubmitField

from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from datetime import datetime
from enum import Enum, auto
from utils import *

import sqlalchemy
import re
import os
import typing


# Auth Grade Enum
class AuthGrade(Enum):
    NONE = 0
    STUDENT = auto()
    INSTRUCTOR = auto()
    ADMIN = auto()


# Debug mode
DEBUG = True

# General configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'txt', 'png', 'jpg', 'jpeg', 'gif'}

# App configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.jinja_env.auto_reload = True

# File configuration
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Crypt initialization
bcrypt = Bcrypt(app)

# Database initialization
db = SQLAlchemy(app)
db.init_app(app)

# Text editor
ckeditor = CKEditor(app)


class PostForm(FlaskForm):
    title = StringField('Title')
    body = CKEditorField('Body')
    submit = SubmitField('Submit')


# ckeditor.init_app(app)


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
    video_path = db.Column(db.String(128), nullable=False)
    thumbnail_path = db.Column(db.String(128), nullable=False)
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
            video_path: {self.video_path}
            thumbnail_path: {self.thumbnail_path}
            category: {self.category}
            sub_category: {self.sub_category}
            last_updated: {self.last_updated}
            price: {self.price}
        '''


##################################
# General functions
##################################
@login_manager.user_loader
def load_user(user_id: int):
    """
    """
    return User.query.get(int(user_id))


def is_logged() -> bool:
    """
    """
    return current_user and current_user.is_authenticated


def get_auth_grade(email: str) -> int:
    """
    """
    user = User.query.filter_by(email=email).first()
    if user:
        return user.auth_grade
    return 0


def validate_email(email: str) -> bool:
    """
    """
    existing_user_username = User.query.filter_by(email=email).first()
    if existing_user_username:
        return False
    return True


def get_courses_by_id(id: int):
    """
    :param id: int
    :return: List[Dict]
    """
    if id:
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
    """
    :return: template
    """

    form = PostForm()

    if request.method == 'POST':
        print(request.values, request.files)
        if 'video' not in request.files or 'thumbnail' not in request.files:
            print('No file part')
            return redirect(request.url)

        for key, file in request.files.items():
            print(key, file)
            if not file.filename:
                print('No image selected for uploading')
                return redirect(request.url)
            else:
                file_name = secure_filename(file.filename)
                file_extension = get_file_ext(file_name)
                if file_extension not in ALLOWED_EXTENSIONS:
                    print(f'You cannot upload file {file_name}, it has an invalid extension!')
                    return redirect(request.url)

                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))

            print(f'The file {file_name} was uploaded succesfully!')

        course = Course(instructor_id=current_user.id,
                        title=request.values['title'],
                        description=form.body.data,
                        video_path=request.files['video'].filename,
                        thumbnail_path=request.files['thumbnail'].filename,
                        category='web',
                        sub_category='python',
                        price=int(request.values['price'])
                        )
        db.session.add(course)
        db.session.commit()

        # return render_template('create.html', context={'file_name': file_name, 'file_extension': file_extension}, form=form)

        print("Course created successfully!")
        return redirect(request.url)

    return render_template('create.html', form=form)


@app.route("/display/<path:file_name>")
def display_attachment(file_name: str):
    """
    """
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], file_name, as_attachment=True
    )


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


from flask_paginate import Pagination, get_page_args
import math


def get_pagination(courses):
    # Get the page from the query string or default to the first page
    # Set the number of items per page
    per_page = 6

    # Get the current page from the query string
    page = request.args.get('page', 1, type=int)

    # Calculate the total number of pages
    total_pages = math.ceil(len(courses) / per_page)

    # Get the courses for the current page
    courses_subset = courses[(page - 1) * per_page: page * per_page]
    return courses_subset, {'page': page, 'pages': total_pages}


@app.route('/get-courses-sub-category/<sub_category>')
def get_courses_by_sub_category(sub_category):
    courses = Course.query.filter_by(sub_category=sub_category).all()
    courses_subset, pagination = get_pagination(courses)
    return render_template('dashboard.html', courses=courses_subset, pagination=pagination)


@app.route('/get-courses-category/<category>')
def get_courses_by_category(category):
    courses = Course.query.filter_by(category=category).all()
    courses_subset, pagination = get_pagination(courses)
    return render_template('dashboard.html', courses=courses_subset, pagination=pagination)


@app.route('/')
def home():
    courses_subset, pagination = get_pagination(get_all_courses())
    if is_logged():
        return render_template('dashboard.html', courses=courses_subset, pagination=pagination)
    else:
        return render_template('index.html', courses=courses_subset, pagination=pagination)


@app.route('/manage_courses')
def manage_courses():
    if is_logged():
        return render_template('manage_courses.html', courses=get_courses_by_id(current_user.id))


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route("/course/<int:id>")
def course(id: int):
    course = Course.query.filter_by(id=id).first()
    return render_template('course.html', course=course)


@app.route('/about')
def about():
    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=DEBUG)

with app.app_context():
    db.create_all()
