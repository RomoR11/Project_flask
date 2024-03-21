from flask import Flask, render_template, request


app = Flask(__name__)
app.config['SECRET_KEY'] = 'adamyauskas'


@app.route('/')
def start():
    return render_template('start.html')


@app.route('/test')
def test():
    return render_template('test.html')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080)
