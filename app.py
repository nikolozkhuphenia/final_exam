from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column(db.String(123), unique=True, nullable=False)
    email = db.Column(db.String(123), unique=True, nullable=False)
    image_file = db.Column(db.String(123), nullable=False, default='default.jpg')
    password = db.Column(db.String(123), nullable=False)
    posts = db.relationship('Post', backref='author')

class Post(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    title = db.Column(db.String(123), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    location = db.Column(db.String(123), nullable=False)
    celery = db.Column(db.String(123), nullable=False)
    company_name = db.Column(db.String(123), nullable=False)
    short_desc = db.Column(db.String(123), nullable=False)
    full_desc = db.Column(db.String(123), nullable=False)

class Item(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(123), unique=False, nullable=False)
    price = db.Column(db.Integer(), nullable=False)
    barcode = db.Column(db.String(123), unique=True, nullable=False)
    description = db.Column(db.String(123), nullable=False)


@app.route('/')
@app.route('/home')
def home_page():

    return render_template('home.html')

@app.route('/about')
def about_page():
    return f'about page'

@app.route('/sign')
def sign_page():
    return f'sign page'

@app.route('/register')
def register_page():
    return f'register page'

@app.route('/market')
def market_page():
    items = [
        {'id': 1, 'name': 'Phone', 'barcode': '893212299897', 'price': 500},
        {'id': 2, 'name': 'Laptop', 'barcode': '123985473165', 'price': 900},
        {'id': 3, 'name': 'Keyboard', 'barcode': '231985128446', 'price': 150}
    ]
    return render_template('market.html', item_name= items)

if __name__ == '__main__':
    app.run(debug=True)