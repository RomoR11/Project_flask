from flask import Flask, render_template
import requests


app = Flask(__name__)
app.config['SECRET_KEY'] = 'adamyauskas'
url = 'https://api.football-data.org/v4/'
headers = {'X-Auth-Token': 'b50fef3995854b77b7233fb3c7134270'}
names_competitions = ['Premier League', 'Primera Division', 'Ligue 1', 'Bundesliga', 'Serie A', 'Eredivisie',
                      'Primeira Liga', 'Championship']
codes_competitions = {'Premier League': 'PL', 'Primera Division': 'PD', 'Ligue 1': 'FL1',
                      'Bundesliga': 'BL1', 'Serie A': 'SA', 'Eredivisie': 'DED', 'Primeira Liga': 'PPL',
                      'Championship': 'ELC'}


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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)