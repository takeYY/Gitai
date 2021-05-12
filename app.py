import os
from flask import Flask, render_template, request, redirect, url_for
from waitress import serve
import pandas as pd

app = Flask(__name__)


def get_hinshi_dict():
    return dict(all='全て(名詞・動詞・形容詞・副詞)', meishi='名詞', doushi='動詞', keiyoushi='形容詞', fukushi='副詞')


def get_edogawa_df():
    return pd.read_csv('csv/edogawa_list.csv')


@app.route('/')
def index():
    # 基本情報
    title = 'ホーム'
    active_url = 'home'
    basic_data = dict(title=title, active_url=active_url)

    return render_template('index.html', basic_data=basic_data)


@app.route('/co-occurrence_network')
def co_occurrence_network():
    # 基本情報
    title = '共起ネットワーク'
    active_url = 'co-oc_network'
    basic_data = dict(title=title, active_url=active_url)
    # 江戸川乱歩作品関連の情報
    novels = get_edogawa_df()
    novels_name = list(novels['name'])
    novels_file_name = list(novels['file_name'])
    novels_tuple = list(zip(novels_name, novels_file_name))
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=novels_tuple)

    return render_template('co-occurrence_network.html', basic_data=basic_data, edogawa_data=edogawa_data)


@app.route('/co-occurrence_network/visualization', methods=['GET', 'POST'])
def network_visualization():
    if not request.method == 'POST':
        # エラーなどでリダイレクトしたい場合
        return redirect(url_for('co_occurrence_network'))

    # 基本情報
    title = '共起ネットワーク'
    active_url = 'co-oc_network'
    basic_data = dict(title=title, active_url=active_url)
    # 江戸川乱歩作品関連の情報
    novels = get_edogawa_df()
    novels_name = list(novels['name'])
    novels_file_name = list(novels['file_name'])
    novels_tuple = list(zip(novels_name, novels_file_name))
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=novels_tuple)
    # 利用者から送られてきた情報を基にデータ整理
    name, file_name = request.form['name'].split('-')
    hinshi_eng, hinshi_jpn = request.form['hinshi'].split('-')
    number = 250 if hinshi_jpn in ['名詞', '動詞', '形容詞', '副詞'] else 1000
    # 可視化HTMLファイルのパスを設定
    EXTERNAL_STATIC_FILE_PATH = os.environ.get('EXTERNAL_STATIC_FILE_PATH')
    visualizer_path = f'{EXTERNAL_STATIC_FILE_PATH}/{file_name}_{hinshi_eng}_{number}.html'
    # 利用者から送られてきた情報を基に送る情報
    sent_data = dict(name=name, hinshi=hinshi_jpn,
                     number=number, path=visualizer_path)

    try:
        return render_template('co-occurrence_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_data)
    except:
        return redirect(url_for('co_occurrence_network'))


# おまじない
if __name__ == "__main__":
    serve(app)
