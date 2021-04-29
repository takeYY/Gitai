from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import pandas as pd
import itertools

app = Flask(__name__)


def get_hinshi_dict():
    return {'all': '全て', 'meishi': '名詞', 'keiyoushi': '形容詞', 'fukushi': '副詞'}


def get_edogawa_df():
    return pd.read_csv('csv/edogawa_list.csv')


@app.route('/')
def index():
    title = '江戸川乱歩作品の共起ネットワーク可視化システム'
    return render_template('index.html', title=title, hinshi_dict=get_hinshi_dict(), edogawa_df=get_edogawa_df())


@app.route('/network_visualization', methods=['GET', 'POST'])
def network_visualization():
    if request.method == 'POST':
        name = request.form['name']
        hinshi = request.form['hinshi']
        number = request.form['number']
        try:
            return render_template(f'network/{name}_{hinshi}_{number}.html')
        except:
            return redirect(url_for('index'))
    else:
        # エラーなどでリダイレクトしたい場合
        return redirect(url_for('index'))


# おまじない
if __name__ == "__main__":
    app.run()
