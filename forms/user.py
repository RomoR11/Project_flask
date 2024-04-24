from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField, BooleanField, FileField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    image = FileField('Загрузить аву (шаву)')
    password = PasswordField('Пароль', validators=[DataRequired()])
    password_again = PasswordField('Повторите пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')


class LoginForm(FlaskForm):
    name = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')


class BonusForm(FlaskForm):
    bonus_string = StringField('Введите промокод', validators=[DataRequired()])
    bonus_submit = SubmitField('Да да я')
