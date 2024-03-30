from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from forms.user import RegisterForm, LoginForm
from data.users import User
from data import db_session


app = Flask(__name__)
app.config['SECRET_KEY'] = 'adamyauskas'
url = 'https://api.football-data.org/v4/'
headers = {'X-Auth-Token': 'b50fef3995854b77b7233fb3c7134270'}
names_competitions = ['Premier League', 'Primera Division', 'Ligue 1', 'Bundesliga', 'Serie A', 'Eredivisie',
                      'Primeira Liga', 'Championship']
codes_competitions = {'Premier League': 'PL', 'Primera Division': 'PD', 'Ligue 1': 'FL1',
                      'Bundesliga': 'BL1', 'Serie A': 'SA', 'Eredivisie': 'DED', 'Primeira Liga': 'PPL',
                      'Championship': 'ELC'}
login_manager = LoginManager()
login_manager.init_app(app)
db_session.global_init("db/users.db")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def start():
    return render_template('main.html')


@app.route('/bonus')
def bonus():
    return render_template('bonus.html')


@app.route('/competitions')
def competitions():
    return render_template('competitions.html', names=names_competitions)


@app.route('/competitions/<code>')
def competition(code):
    if code in codes_competitions.values():
        teams = []
        response = requests.get(url=f'{url}/competitions/{code}/standings', headers=headers).json()['standings'][0]
        for team in response['table']:
            teams.append((team['position'], team['team']['shortName'], team['team']['crest'], team['playedGames'],
                          team['won'], team['draw'], team['lost'], team['points']))
        return render_template(f'{code}.html', names=names_competitions, teams=teams, length=len(teams))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.name.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(name=form.name.data, amount_of_money=1000)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)