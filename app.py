import os
from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import pandas as pd
import itertools

app = Flask(__name__)


def get_hinshi_dict():
    return {'all': '全て(名詞・動詞・形容詞・副詞)', 'meishi': '名詞', 'doushi': '動詞', 'keiyoushi': '形容詞', 'fukushi': '副詞'}


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
        name, file_name = request.form['name'].split('-')
        hinshi_eng, hinshi_jpn = request.form['hinshi'].split('-')
        number = 250 if hinshi_jpn in ['名詞', '動詞', '形容詞', '副詞'] else 1000
        EXTERNAL_STATIC_FILE_PATH = os.environ.get('EXTERNAL_STATIC_FILE_PATH')
        request_path = f'{EXTERNAL_STATIC_FILE_PATH}/{file_name}_{hinshi_eng}_{number}.html'
        request_data = {'name': name, 'hinshi': hinshi_jpn, 'number': number}
        try:
            return render_template('index.html', title=title, hinshi_dict=get_hinshi_dict(), edogawa_df=get_edogawa_df(), request_path=request_path, request_data=request_data)
        except:
            return redirect(url_for('index'))
    else:
        # エラーなどでリダイレクトしたい場合
        return redirect(url_for('index'))


# おまじない
if __name__ == "__main__":
    app.run()
