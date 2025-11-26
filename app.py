from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from forms import RegistrationForm, LoginForm, UserForm, PostForm
import logging
from logging.handlers import RotatingFileHandler
import os

# -----------------------
# App and Database Setup
# -----------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'f3d4340e1137bbd0f08ecd55722cb8a4'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# -----------------------
# Logging Setup
# -----------------------
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/app.log', maxBytes=1_000_000, backupCount=5)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# -----------------------
# Login Manager
# -----------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

# -----------------------
# Models
# -----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column(db.String(123), unique=True, nullable=False)
    email = db.Column(db.String(123), unique=True, nullable=False)
    image_file = db.Column(db.String(123), nullable=False, default='default.jpg')
    password = db.Column(db.String(123), nullable=False)
    posts = db.relationship('Post', backref='author')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

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

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

class Users(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    name = db.Column(db.String(123), unique=True, nullable=False)
    email = db.Column(db.String(123), unique=True, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def __repr__(self):
        return f"<User {self.name}>"

# -----------------------
# User Loader
# -----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -----------------------
# Routes
# -----------------------
@app.route('/')
@app.route('/index')
def index_page():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('index.html', posts=posts)

@app.route('/about')
def about_page():
    return render_template('about.html')

# -----------------------
# Authentication
# -----------------------
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            app.logger.info(f"Successful login: {user.email}")
            flash(f'თქვენ წარმატებით გაიარეთ', 'success')
            return redirect(url_for('profile'))
        else:
            app.logger.warning(f"Failed login attempt: {form.email.data}")
            flash("არასწორია", "danger")
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('index_page'))

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f'მომხმარებელი წარმატებით შეიქმნა {form.username.data}', 'success')
        app.logger.info(f"User registered: {form.username.data}")
        return redirect(url_for('login_page'))
    return render_template('register.html', title='Register', form=form)

# -----------------------
# Profile
# -----------------------
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # User profile form
    user_form = UserForm(obj=current_user)
    post_form = PostForm()

    # Update profile info
    if 'update_profile' in request.form and user_form.validate():
        current_user.username = user_form.name.data
        current_user.email = user_form.email.data
        db.session.commit()
        flash("Profile updated successfully", "success")
        app.logger.info(f"Profile updated: {current_user.username}")
        return redirect(url_for('profile'))

    # Add new post
    if 'add_post' in request.form and post_form.validate():
        new_post = Post(
            title=post_form.title.data,
            user_id=current_user.id,
            location=post_form.location.data,
            celery=post_form.celery.data,
            company_name=post_form.company_name.data,
            short_desc=post_form.short_desc.data,
            full_desc=post_form.full_desc.data
        )
        db.session.add(new_post)
        db.session.commit()
        flash(f"Post '{new_post.title}' created successfully!", "success")
        app.logger.info(f"Post added: {new_post.title} by user {current_user.username}")
        return redirect(url_for('profile'))

    # Show user's posts
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.date_posted.desc()).all()
    return render_template('profile.html', user_form=user_form, post_form=post_form, posts=posts)

# -----------------------
# Edit Post
# -----------------------
@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post = Post.query.get_or_404(id)
    form = PostForm(obj=post)
    if request.method == 'POST' and form.validate():
        post.title = form.title.data
        post.location = form.location.data
        post.celery = form.celery.data
        post.company_name = form.company_name.data
        post.short_desc = form.short_desc.data
        post.full_desc = form.full_desc.data
        db.session.commit()
        flash("Post updated successfully!", "success")
        app.logger.info(f"Post edited: {post.title} by user {current_user.username}")
        return redirect(url_for('profile'))
    return render_template('edit_post.html', form=form, post=post)

# -----------------------
# Delete Post
# -----------------------
@app.route('/delete_post/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    flash(f"Post '{post.title}' deleted successfully", "success")
    app.logger.info(f"Post deleted: {post.title} by user {current_user.username}")
    return redirect(url_for('profile'))

# -----------------------
# Error Handling Example for API request
# -----------------------
@app.route('/api_example')
def api_example():
    import requests
    try:
        response = requests.get('https://some-api.com/data')
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        flash("API request failed", "danger")
        app.logger.error(f"API request error: {e}")
        return redirect(url_for('index_page'))

# -----------------------
# Run app
# -----------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))  # Use Render's port, default to 5000 locally
    app.run(host='0.0.0.0', port=port)