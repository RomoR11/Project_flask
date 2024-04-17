from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_user, login_required, logout_user
import requests
from forms.user import RegisterForm, LoginForm
from forms.bet import BetForm
from data.users import User
from data.bets import Bets
from data import db_session
import datetime as dt


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
# user = Bets()
# user.match_id = "444566"
# user.bet = ""
# user.email = "email@email.ru"
# user.user_id = 1
# db_sess = db_session.create_session()
# db_sess.add(user)
# db_sess.commit()


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def start():
    matches = []
    time_from, time_to = dt.datetime.now().date(), dt.datetime.now().date() + dt.timedelta(days=5)
    response = requests.get(url=f'{url}/matches/?dateFrom={time_from}&dateTo={time_to}', headers=headers).json()
    for i in response['matches']:
        if i['competition']['code'] in codes_competitions.values():
            date, time = f"{i['utcDate'].split('T')[0]}", f"{i['utcDate'].split('T')[1][:5]}"
            matches.append((i["homeTeam"]["shortName"], i["homeTeam"]["crest"],
                            i["awayTeam"]["shortName"], i["awayTeam"]["crest"], (date, time), i['id']))
    return render_template('main.html', matches=matches, length=len(matches))


@app.route('/bet/<match>', methods=['GET', 'POST'])
def bet(match):
    form = BetForm()
    response = requests.get(url=f'{url}/matches/{match}', headers=headers).json()
    form.bet.choices = [(response["homeTeam"]["shortName"], response["homeTeam"]["shortName"]),
                        ('Ничья', 'Ничья'),
                        (response["awayTeam"]["shortName"], response["awayTeam"]["shortName"])]
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.name == form.user_name.data).first()
    if form.validate_on_submit():
        if int(form.bet_money.data) > user.amount_of_money:
            return render_template('create_bet.html',
                                   form=form,
                                   message="У вас недостаточно денег, нужен деп!")
        user_bet = Bets()
        user_bet.match_id = match
        user_bet.user_id = user.id
        user_bet.bet = form.bet.data
        user_bet.bet_money = form.bet_money.data
        db_sess.add(user_bet)
        db_sess.commit()
        return redirect('/')
    return render_template('create_bet.html', form=form)


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
    print(form.validate_on_submit())
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


@app.route('/user_bets')
def user_bets():
    db_sess = db_session.create_session()
    bets = []
    for i in db_sess.query(Bets).filter(Bets.user_id == User.id):
        response = requests.get(url=f'{url}/matches/{i.match_id}', headers=headers).json()
        date = f"{response['utcDate'].split('T')[0]} {response['utcDate'].split('T')[1][:5]}"
        bets.append((response["homeTeam"]["shortName"], response["homeTeam"]["crest"],
                     response["awayTeam"]["shortName"], response["awayTeam"]["crest"],
                     date, response["score"]["winner"], i.bet))
    return render_template("bets.html", bets=bets, length=len(bets))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)