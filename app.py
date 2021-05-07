import os
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
        title = '江戸川乱歩作品の共起ネットワーク可視化システム'
        name = request.form['name']
        hinshi = request.form['hinshi']
        number = request.form['number']
        EXTERNAL_STATIC_FILE_PATH = os.environ.get('EXTERNAL_STATIC_FILE_PATH')
        request_path = f'{EXTERNAL_STATIC_FILE_PATH}/{name}_{hinshi}_{number}.html'
        try:
            return render_template('index.html', title=title, hinshi_dict=get_hinshi_dict(), edogawa_df=get_edogawa_df(), request_path=request_path)
        except:
            return redirect(url_for('index'))
    else:
        # エラーなどでリダイレクトしたい場合
        return redirect(url_for('index'))


# おまじない
if __name__ == "__main__":
    app.run()
