from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField
from wtforms.validators import Email, DataRequired, Length, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Email(), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=15)])
    email = StringField('Email', validators=[Email(), DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class UserForm(FlaskForm):
    name = StringField('Username', validators=[DataRequired(), Length(max=15)])
    email = StringField('Email', validators=[Email(), DataRequired()])
    submit = SubmitField('Add User')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    celery = StringField('Celery', validators=[DataRequired()])
    company_name = StringField('Company Name', validators=[DataRequired()])
    short_desc = TextAreaField('Short Description', validators=[DataRequired()])
    full_desc = TextAreaField('Full Description', validators=[DataRequired()])
    submit = SubmitField('Add Post')