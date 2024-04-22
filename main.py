from flask import Flask, render_template, request, redirect, make_response
from flask_login import LoginManager, login_user, login_required, logout_user
import requests
from werkzeug.utils import secure_filename
from forms.user import RegisterForm, LoginForm, BonusForm
from forms.bet import BetForm
from data.users import User
from data.bets import Bets
from data import db_session
import datetime as dt
import time as t


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
USER_NAME = ''
BONUSES = {}
login_manager.init_app(app)
db_session.global_init("db/users.db")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
def start():
    global BONUSES
    visits_count = int(request.cookies.get("visits_count", 0))
    if visits_count:
        res = make_response('visits_count + 1')
        res.set_cookie("visits_count", str(visits_count + 1),
                       max_age=60 * 60 * 24 * 5)
    else:
        res = make_response('visits_count')
        res.set_cookie("visits_count", '1',
                       max_age=60 * 60 * 24 * 5)
    BONUSES = {'Никита Сергеевич': False, 'Chakra77': False,
               "DenCor's": False, 'Яна Цист': False, '1488': False, 'Вентилятор': False}
    matches = []
    time_from, time_to = dt.datetime.now().date(), dt.datetime.now().date() + dt.timedelta(days=5)
    response = requests.get(url=f'{url}/matches/?dateFrom={time_from}&dateTo={time_to}', headers=headers).json()
    if 'message' in response.keys():
        t.sleep(int(response['message'][-11:-9]))
        response = requests.get(url=f'{url}/matches/?dateFrom={time_from}&dateTo={time_to}', headers=headers).json()
    for i in response['matches']:
        if i['competition']['code'] in codes_competitions.values():
            date, time = f"{i['utcDate'].split('T')[0]}", f"{i['utcDate'].split('T')[1][:5]}"
            cr_date = dt.datetime.strptime(date + time, '%Y-%m-%d%H:%M')
            date_now = dt.datetime.now()
            if cr_date > date_now:
                matches.append((i["homeTeam"]["shortName"], i["homeTeam"]["crest"],
                                i["awayTeam"]["shortName"], i["awayTeam"]["crest"], (date, time), i['id']))
    return render_template('main.html', matches=matches, length=len(matches))


@app.route('/bet/<match>', methods=['GET', 'POST'])
def bet(match):
    form = BetForm()
    response = requests.get(url=f'{url}/matches/{match}', headers=headers).json()
    if 'message' in response.keys():
        t.sleep(int(response['message'][-11:-9]))
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
        user.amount_of_money -= int(form.bet_money.data)
        db_sess.commit()
        return redirect('/')
    return render_template('create_bet.html', form=form)


@app.route('/bonus', methods=['GET', 'POST'])
def bonus():
    global USER_NAME, BONUSES
    form = BonusForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == USER_NAME).first()
        if not BONUSES[form.bonus_string.data] and form.bonus_string.data == 'Никита Сергеевич':
            BONUSES[form.bonus_string.data] = True
            salary = user.amount_of_money
            user.amount_of_money = salary + 100000
            db_sess.commit()
        elif not BONUSES[form.bonus_string.data] and form.bonus_string.data == '1488':
            BONUSES[form.bonus_string.data] = True
            salary = user.amount_of_money
            user.amount_of_money = salary + 1488
            db_sess.commit()
        if not BONUSES[form.bonus_string.data]:
            BONUSES[form.bonus_string.data] = True
            salary = user.amount_of_money
            user.amount_of_money = salary + 1000
            db_sess.commit()
    return render_template('bonus.html', form=form)


@app.route('/competitions')
def competitions():
    return render_template('competitions.html', names=names_competitions)


@app.route('/competitions/<code>')
def competition(code):
    if code in codes_competitions.values():
        teams = []
        response = requests.get(url=f'{url}/competitions/{code}/standings', headers=headers).json()['standings'][0]
        if 'message' in response.keys():
            t.sleep(int(response['message'][-11:-9]))
            response = requests.get(url=f'{url}/competitions/{code}/standings', headers=headers).json()['standings'][0]
        for team in response['table']:
            teams.append((team['position'], team['team']['shortName'], team['team']['crest'], team['playedGames'],
                          team['won'], team['draw'], team['lost'], team['points']))
        return render_template(f'{code}.html', names=names_competitions, teams=teams, length=len(teams))


@app.route('/profile')
def profile():
    global USER_NAME
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.name == USER_NAME).first()
    img = user.image if user.image else False
    return render_template('profile.html', title='Профиль',
                           name=user.name, created_date=user.created_date,
                           amount_of_money=user.amount_of_money, image=img)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/login', methods=['GET', 'POST'])
def login():
    global USER_NAME, BONUSES
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.name.data).first()
        if user and user.check_password(form.password.data):
            USER_NAME = user.name
            BONUSES = {'Никита Сергеевич': False, 'Chakra77': False,
                       "DenCor's": False, 'Яна Цист': False, '1488': False, 'Вентилятор': False}
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
        if not form.image.data.filename.endswith(('.jpeg', '.png', '.jpg')) and form.image.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Это не ава")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.name == form.name.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User()
        user.name = form.name.data
        user.amount_of_money = 1000
        if form.image.data:
            filename = secure_filename(form.image.data.filename)
            form.image.data.save('static/avatars/' + filename)
            user.image = 'static/avatars/' + filename
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


def win_bet(money, cr_bet):
    global USER_NAME
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.name == USER_NAME).first()
    user.amount_of_money += int(money) * 2 if cr_bet != 'Ничья' else int(money) + int(money) // 2
    db_sess.commit()


@app.route('/user_bets')
def user_bets():
    global USER_NAME
    db_sess = db_session.create_session()
    bets = []
    user = db_sess.query(User).filter(User.name == USER_NAME).first()
    for i in db_sess.query(Bets).filter(Bets.user_id == user.id):
        win = 0
        response = requests.get(url=f'{url}/matches/{i.match_id}', headers=headers).json()
        if 'message' in response.keys():
            t.sleep(int(response['message'][-11:-9]))
            response = requests.get(url=f'{url}/matches/{i.match_id}', headers=headers).json()
        date = f"{response['utcDate'].split('T')[0]} {response['utcDate'].split('T')[1][:5]}"
        if (i.bet == response["homeTeam"]["shortName"] and response["score"]["winner"] == 'HOME_TEAM' or
                i.bet == response["awayTeam"]["shortName"] and response["score"]["winner"] == 'AWAY_TEAM' or
                i.bet == 'Ничья' and response["score"]["winner"] == 'DRAW') and \
                response["status"] == 'FINISHED':
            win_bet(i.bet_money, i.bet)
            win = 1
        elif response["status"] != 'FINISHED':
            win = 0
        else:
            win = 2
        bets.append((response["homeTeam"]["shortName"], response["homeTeam"]["crest"],
                     response["awayTeam"]["shortName"], response["awayTeam"]["crest"],
                     date, win, i.bet, i.bet_money))
        if response["status"] == 'FINISHED':
            db_sess.delete(i)
            db_sess.commit()
    return render_template("bets.html", bets=bets, length=len(bets))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
