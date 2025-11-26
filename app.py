from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging
import os

from forms import RegistrationForm, LoginForm, UserForm, PostForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'f3d4340e1137bbd0f08ecd55722cb8a4'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db = SQLAlchemy(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

# Logging setup
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Models

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    username = db.Column(db.String(123), unique=True, nullable=False)
    email = db.Column(db.String(123), unique=True, nullable=False)
    password = db.Column(db.String(123), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"


class Post(db.Model):
    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    title = db.Column(db.String(), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.now)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(), nullable=False)
    celery = db.Column(db.Integer(), nullable=False)
    company_name = db.Column(db.String(), nullable=False)
    short_desc = db.Column(db.String(), nullable=False)
    full_desc = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes

@app.route('/')
@app.route('/index')
def index_page():
    posts = Post.query.order_by(Post.date_posted.desc()).all()
    return render_template('index.html', posts=posts)


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'User {form.username.data} created successfully', 'success')
        return redirect(url_for('login_page'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('You have logged in successfully', 'success')
            logging.info(f"Successful login: {user.email}")
            return redirect(url_for('profile'))
        else:
            flash("Invalid email or password", 'danger')
            logging.warning(f"Failed login attempt: {form.email.data}")
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
@login_required
def logout():
    logging.info(f"User logged out: {current_user.email}")
    logout_user()
    flash("You have logged out", "success")
    return redirect(url_for('index_page'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Forms
    form = UserForm(obj=current_user)
    post_form = PostForm()

    if request.method == 'POST':
        # PROFILE UPDATE
        if 'update_user' in request.form:
            if form.validate():
                current_user.username = form.name.data
                current_user.email = form.email.data
                db.session.commit()
                flash("Profile updated successfully!", "success")
                logging.info(f"Profile updated: {current_user.email}")
                return redirect(url_for('profile'))
            else:
                flash("Profile update failed!", "danger")

        # ADD POST
        elif 'add_post' in request.form:
            if post_form.validate():
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
                logging.info(f"Post added: {new_post.title} by {current_user.email}")
                return redirect(url_for('profile'))
            else:
                print(post_form.errors)
                flash("Failed to add post. Please check your fields.", "danger")

    # GET request or after POST redirect
    user_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.date_posted.desc()).all()
    return render_template('profile.html', form=form, post_form=post_form, posts=user_posts)


@app.route('/post/delete/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        flash("You cannot delete this post!", "danger")
        return redirect(url_for('profile'))
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted successfully!", "success")
    logging.info(f"Post deleted: {post.title} by {current_user.email}")
    return redirect(url_for('profile'))


@app.route('/post/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update_post(id):
    post = Post.query.get_or_404(id)
    if post.author != current_user:
        flash("You cannot edit this post!", "danger")
        return redirect(url_for('profile'))

    form = PostForm(obj=post)

    if form.validate_on_submit():
        post.title = form.title.data
        post.location = form.location.data
        post.celery = form.celery.data
        post.company_name = form.company_name.data
        post.short_desc = form.short_desc.data
        post.full_desc = form.full_desc.data
        db.session.commit()
        flash("Post updated successfully!", "success")
        logging.info(f"Post updated: {post.title} by {current_user.email}")
        return redirect(url_for('profile'))

    return render_template('edit_post.html', form=form, post=post)


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
        post.user_id = current_user.id
        db.session.commit()
        flash("Post updated successfully!", "success")
        logging.info(f"Post updated: {post.title} by {current_user.email}")
        return redirect(url_for('profile'))

    return render_template('edit_post.html', form=form, post=post)


# Run

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)