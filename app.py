from flask import Flask, request, redirect, render_template
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
    STUDENT = 0
    INSTRUCTOR = 1
    ADMIN = 2


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

# Crypt configuration
bcrypt = Bcrypt(app)

# Db initialization
db = SQLAlchemy(app)
db.init_app(app)


# table instructor
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(50))
    password = db.Column(db.String(32))
    email = db.Column(db.String(100), nullable=False)
    date_joined = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    auth_grade = db.Column(db.Integer, nullable=False, default=AuthGrade.STUDENT)

    def __repr__(self):
        return f'<User: {self.email}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Register Form Class
class RegisterForm(FlaskForm):
    username = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField(validators=[
        InputRequired(), Length(min=8, max=30)])

    password = PasswordField(validators=[
        InputRequired(), Length(min=4, max=32)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    print_error(request.values)

    if request.method == 'POST':
        full_name = request.form['full_name']
        password = request.form['password']
        email = request.form['email']
        auth_grade = int(request.form['checkbox'])

        user = User(full_name=full_name, password=password, email=email, auth_grade=auth_grade)
        try:
            db.session.add(user)
            db.session.commit()
            return redirect('/')
        except BaseException as f:
            return f'There was an issue with registration. {f}'

    return render_template('register.html', content={i.name: i.value for i in AuthGrade})

@app.route('/')
def home():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=DEBUG)

with app.app_context():
    db.create_all()
