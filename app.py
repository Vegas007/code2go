from flask import Flask, request, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum
from utils import *
import re

DEBUG = True
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True

app.jinja_env.auto_reload = True

db = SQLAlchemy(app)
db.init_app(app)


class AuthGrade(Enum):
    STUDENT = 0
    INSTRUCTOR = 1
    ADMIN = 2


# table instructor
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(50))
    password = db.Column(db.String(32))
    email = db.Column(db.String(100))
    date_joined = db.Column(db.Date, default=datetime.utcnow)
    auth_grade = db.Column(db.Integer)

    def __repr__(self):
        return f'<User: {self.email}>'


def home():
    return render_template('index.html')


def login():
    return render_template('login.html')


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


if __name__ == '__main__':
    app.run(debug=DEBUG)

with app.app_context():
    db.create_all()

app.add_url_rule('/', 'home', home)
app.add_url_rule('/login', 'login', login)
