from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired


class BetForm(FlaskForm):
    user_name = StringField('Введите свой логин', validators=[DataRequired()])
    bet = SelectField('Ставка:')
    bet_money = StringField('Введите сумму ставки', validators=[DataRequired()])
    submit = SubmitField('Сделать ставку')
