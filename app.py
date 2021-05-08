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
    title = 'ホーム'
    active_url = 'home'
    return render_template('index.html', title=title, active_url=active_url)


@app.route('/co-occurrence_network')
def co_occurrence_network():
    title = '共起ネットワーク'
    active_url = 'co-oc_network'
    return render_template('co-occurrence_network.html', title=title, active_url=active_url, hinshi_dict=get_hinshi_dict(), edogawa_df=get_edogawa_df())


@app.route('/co-occurrence_network/visualization', methods=['GET', 'POST'])
def network_visualization():
    if request.method == 'POST':
        title = '共起ネットワーク'
        active_url = 'co-oc_network'
        name, file_name = request.form['name'].split('-')
        hinshi_eng, hinshi_jpn = request.form['hinshi'].split('-')
        number = 250 if hinshi_jpn in ['名詞', '動詞', '形容詞', '副詞'] else 1000
        EXTERNAL_STATIC_FILE_PATH = os.environ.get('EXTERNAL_STATIC_FILE_PATH')
        request_path = f'{EXTERNAL_STATIC_FILE_PATH}/{file_name}_{hinshi_eng}_{number}.html'
        request_data = {'name': name, 'hinshi': hinshi_jpn, 'number': number}
        try:
            return render_template('co-occurrence_network.html', title=title, active_url=active_url, hinshi_dict=get_hinshi_dict(), edogawa_df=get_edogawa_df(), request_path=request_path, request_data=request_data)
        except:
            return redirect(url_for('co_occurrence_network'))
    else:
        # エラーなどでリダイレクトしたい場合
        return redirect(url_for('co_occurrence_network'))


# おまじない
if __name__ == "__main__":
    app.run()
