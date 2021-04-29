from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/')
def hello():
    name = 'テストユーザー'
    return render_template('index.html', title='test', name=name)


@app.route('/post', methods=['GET', 'POST'])
def post():
    if request.method == 'POST':
        name = request.form['name']
        return render_template('index.html', name=name)
    else:
        # エラーなどでリダイレクトしたい場合
        return redirect(url_for('index'))


# おまじない
if __name__ == "__main__":
    app.run()
