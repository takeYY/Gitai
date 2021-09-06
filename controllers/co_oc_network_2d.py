from flask import Blueprint, render_template, request, redirect, url_for, flash
from get_data import get_basic_data, get_novels_tuple, get_hinshi_dict
from co_oc_network import create_network, get_csv_filename


network2d__page = Blueprint(
    'network_2d', __name__, url_prefix='/2d-co-oc-network')


@network2d__page.route('', methods=['GET', 'POST'])
def show():
    """
    共起ネットワーク

    """
    # 基本情報
    basic_data = get_basic_data(title='共起ネットワーク', active_url='co-oc_network')
    # 江戸川乱歩作品関連の情報
    hinshi_dict = get_hinshi_dict()
    edogawa_data = dict(hinshi_dict=hinshi_dict,
                        name_file=get_novels_tuple(col1='name', col2='file_name'))
    if request.method == 'GET':
        return render_template('co-occurrence_network.html', basic_data=basic_data, edogawa_data=edogawa_data)

    # 利用者から送られてきた情報
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
            name, file_name, error = get_csv_filename(request)
    else:
        # 利用者から送られてきた情報を基にデータ整理
        name, file_name = request.form['name'].split('-')
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
        sent_error_data = dict(input_type=input_type, name=name, number=number, hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                               remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words)
        return render_template('co-occurrence_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_error_data)
    # 共起ネットワーク作成
    try:
        csv_file_name, co_oc_df = create_network(file_name=file_name, target_hinshi=hinshi_jpn, target_num=number,
                                                 remove_words=remove_words, remove_combi=remove_combi_dict,
                                                 target_words=target_words, input_type=input_type)
    except:
        flash('ファイル形式が正しくありません。（入力形式に沿ってください）', 'error')
        sent_error_data = dict(input_type=input_type, name=name, number=number, hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                               remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words)
        return render_template('co-occurrence_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_error_data)
    # 利用者から送られてきた情報を基に送る情報
    sent_data = dict(input_type=input_type, name=name, prev_csv_name=file_name, file_name=csv_file_name, number=number, hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                     remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words, co_oc_df=co_oc_df)

    try:
        return render_template('co-occurrence_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_data)
    except:
        return redirect(url_for('co_occurrence_network'))
