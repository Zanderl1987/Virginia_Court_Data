from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField
from wtforms.validators import InputRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    username = StringField('',validators=[InputRequired(), Length(min=4, max=29)], render_kw={"placeholder": "Username"})
    password = PasswordField('',validators=[InputRequired(), Length(min=8, max=45)], render_kw={"placeholder": "Password"})
    remember = BooleanField('Remember me')

class RequestResetForm(FlaskForm):
    email = StringField('', validators=[InputRequired(),Email()], render_kw={"placeholder": "Email"})
    
class ResetPasswordForm(FlaskForm):
    password = PasswordField('',validators=[InputRequired(), Length(min=8, max=45)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField('',validators=[InputRequired(), EqualTo('password')], render_kw={"placeholder": "Confirm Password"})