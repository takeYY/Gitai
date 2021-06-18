import os
from flask import Flask, render_template, request, redirect, url_for, send_file, send_from_directory
from waitress import serve
from get_data import get_hinshi_dict, get_khcoder_df, get_basic_data, get_novels_tuple, get_edogawa_merge_df
from co_oc_network import create_network

app = Flask(__name__)


@app.route('/')
def index():
    """
    ホーム

    """
    # 基本情報
    basic_data = get_basic_data()

    return render_template('index.html', basic_data=basic_data)


@app.route('/information')
def information():
    """
    作品情報

    """
    # 基本情報
    basic_data = get_basic_data(title='作品情報', active_url='information')
    # 江戸川乱歩作品関連の情報
    edogawa_merge_df = get_edogawa_merge_df()

    return render_template('information.html', basic_data=basic_data, edogawa_merge_df=edogawa_merge_df)


@app.route('/co-occurrence_network')
def co_occurrence_network():
    """
    共起ネットワーク

    """
    # 基本情報
    basic_data = get_basic_data(title='共起ネットワーク', active_url='co-oc_network')
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name', col2='file_name'))

    return render_template('co-occurrence_network.html', basic_data=basic_data, edogawa_data=edogawa_data)


@app.route('/co-occurrence_network/visualization', methods=['GET', 'POST'])
def network_visualization():
    """
    共起ネットワーク（「可視化」ボタン押下後）

    """
    # エラーなどでリダイレクトしたい場合
    if not request.method == 'POST':
        return redirect(url_for('co_occurrence_network'))

    # 基本情報
    basic_data = get_basic_data(title='共起ネットワーク', active_url='co-oc_network')
    # 江戸川乱歩作品関連の情報
    hinshi_dict = get_hinshi_dict()
    edogawa_data = dict(hinshi_dict=hinshi_dict,
                        name_file=get_novels_tuple(col1='name', col2='file_name'))
    # 利用者から送られてきた情報を基にデータ整理
    name, file_name = request.form['name'].split('-')
    number = int(request.form['number'])
    hinshi_eng = request.form.getlist('hinshi')
    hinshi_jpn = [hinshi_dict.get(k) for k in hinshi_eng]
    remove_words = request.form['remove-words']
    # 共起ネットワーク作成
    now, co_oc_df = create_network(file_name=file_name, target_hinshi=hinshi_jpn,
                                   target_num=number, remove_words=remove_words)
    # 利用者から送られてきた情報を基に送る情報
    sent_data = dict(name=name, file_name=now, number=number, hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                     remove_words=remove_words, co_oc_df=co_oc_df)

    try:
        return render_template('co-occurrence_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_data)
    except:
        return redirect(url_for('co_occurrence_network'))


@app.route('/co-occurrence_network/visualization/<file_name>')
def show_co_oc_network(file_name):
    """
    共起ネットワーク用htmlファイル

    """
    return send_file(f'tmp/{file_name}.html')


@app.route('/khcoder', methods=['GET', 'POST'])
def khcoder():
    """
    KH Coder

    """
    # 基本情報
    basic_data = get_basic_data(title='KH Coder', active_url='KH-coder')
    # 江戸川乱歩作品関連の情報
    novels_data = get_novels_tuple(col1='name', col2='file_name')

    if request.method == 'GET':
        return render_template('khcoder.html', basic_data=basic_data, novels_data=novels_data)
    else:
        # 利用者から送られてきた情報を基にデータ整理
        name, file_name = request.form['name'].split('-')
        sent_data = dict(name=name, file_name=file_name,
                         text_chapter=get_novels_tuple(novels=get_khcoder_df(file_name), col1='テキスト', col2='章'))

        return render_template('khcoder.html', basic_data=basic_data, novels_data=novels_data, sent_data=sent_data)


@app.route('/download/csv', methods=['POST'])
def download_csv():
    """
    csvデータのダウンロード

    """
    dir_path = request.form.get('dir_path')
    file_name = request.form.get('file_name')
    new_name = request.form.get('new_name')

    return send_from_directory(
        dir_path,
        f'{file_name}.csv',
        as_attachment=True,
        attachment_filename=f'{new_name}.csv',
    )


# おまじない
if __name__ == "__main__":
    serve(app)
