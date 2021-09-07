from co_oc_3d_network import create_3d_network
from flask import flash, render_template, request, redirect, url_for
from waitress import serve
from get_data import get_hinshi_dict, get_basic_data, get_novels_tuple
from co_oc_network import create_network, get_csv_filename
import os
from route import app

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 16MBにデータ制限
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# SECRET_KEYを設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


@app.route('/co-oc-network', methods=['GET', 'POST'])
def co_oc_network():
    """
    共起ネットワーク

    """
    # 基本情報
    basic_data = get_basic_data(
        title='共起ネットワーク', active_url='co_oc_network')
    # 江戸川乱歩作品関連の情報
    hinshi_dict = get_hinshi_dict()
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name', col2='file_name'))

    if request.method == 'GET':
        return render_template('co_oc_network.html', basic_data=basic_data, edogawa_data=edogawa_data)

    # 利用者から送られてきた情報
    dimension = int(request.form['dimension'])
    number = int(request.form['number'])
    hinshi_eng = request.form.getlist('hinshi')
    hinshi_jpn = [hinshi_dict.get(k) for k in hinshi_eng]
    remove_words = request.form['remove-words']
    remove_combi_meishi = request.form.getlist('remove-combi-meishi')
    remove_combi_doushi = request.form.getlist('remove-combi-doushi')
    remove_combi_keiyoushi = request.form.getlist('remove-combi-keiyoushi')
    remove_combi_fukushi = request.form.getlist('remove-combi-fukushi')
    remove_combi_dict = dict(meishi=remove_combi_meishi, doushi=remove_combi_doushi,
                             keiyoushi=remove_combi_keiyoushi, fukushi=remove_combi_fukushi)
    target_words = request.form['target-words']
    # エラーの有無判定
    error = False
    # 入力データ
    input_type = request.form['input_type']
    if input_type == 'csv':
        if request.form.get('previous_file_name'):
            name = request.form['previous_file_name']
            file_name = request.form['previous_file_path']
        else:
            name, file_name, error = get_csv_filename(app, request)
        used_category = 0
    else:
        # 利用者から送られてきた情報を基にデータ整理
        name, file_name = request.form['name'].split('-')
        used_category = int(request.form['is_used_category'])
    name = name.replace(' ', '')
    # 品詞が1つも選択されなかった場合
    if not hinshi_eng:
        flash('品詞が選択されていません。', 'error')
        error = True
    # 共起数が0以下だった場合
    if number < 1:
        flash('共起数が少なすぎます。', 'error')
        error = True
    # errorがあれば
    if error:
        sent_error_data = dict(input_type=input_type, name=name, dimension=dimension, number=number,
                               hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                               remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words,
                               is_used_category=used_category)
        return render_template('co_oc_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_error_data)
    # 共起ネットワーク作成
    is_used_3d = True if dimension == 3 else False
    try:
        csv_file_name, co_oc_df = create_network(file_name=file_name, target_hinshi=hinshi_jpn, target_num=number,
                                                 remove_words=remove_words, remove_combi=remove_combi_dict,
                                                 target_words=target_words, input_type=input_type,
                                                 is_used_3d=is_used_3d, used_category=used_category)
        if is_used_3d:
            html_file_name = create_3d_network(
                co_oc_df, target_num=number, used_category=used_category)
        else:
            html_file_name = csv_file_name
    except:
        flash('ファイル形式が正しくありません。（入力形式に沿ってください）', 'error')
        sent_error_data = dict(input_type=input_type, name=name, dimension=dimension, number=number,
                               hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                               remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words,
                               is_used_category=used_category)
        return render_template('co_oc_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_error_data)
    # 利用者から送られてきた情報を基に送る情報
    sent_data = dict(input_type=input_type, name=name,
                     prev_csv_name=file_name, file_name=csv_file_name, html_file_name=html_file_name,
                     dimension=dimension, number=number, hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                     remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words,
                     co_oc_df=co_oc_df, is_used_category=used_category)

    try:
        return render_template('co_oc_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_data)
    except:
        return redirect(url_for('co_oc_network'))


@app.errorhandler(404)
def not_found(error):
    return redirect(url_for('index.show'), code=200)


# おまじない
if __name__ == "__main__":
    serve(app)
