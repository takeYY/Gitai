from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from get_data import get_basic_data, get_novels_tuple, get_hinshi_dict
from co_oc_network import create_network, get_csv_filename
from co_oc_3d_network import create_3d_network


network_page = Blueprint(
    'network', __name__, url_prefix='/rikkyo-edogawa/co-oc-network')


@network_page.route('', methods=['GET', 'POST'])
def show():
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
        session.clear()
        return render_template('co_oc_network.html', basic_data=basic_data, edogawa_data=edogawa_data)

    # 利用者から送られてきた情報
    dimension = int(request.form.get('dimension'))
    input_type = request.form.get('input_type')
    number = int(request.form.get('number'))
    hinshi_eng = request.form.getlist('hinshi')
    hinshi_jpn = [hinshi_dict.get(k) for k in hinshi_eng]
    remove_words = request.form.get('remove-words')
    remove_combi_meishi = request.form.getlist('remove-combi-meishi')
    remove_combi_doushi = request.form.getlist('remove-combi-doushi')
    remove_combi_keiyoushi = request.form.getlist('remove-combi-keiyoushi')
    remove_combi_fukushi = request.form.getlist('remove-combi-fukushi')
    remove_combi_dict = dict(meishi=remove_combi_meishi, doushi=remove_combi_doushi,
                             keiyoushi=remove_combi_keiyoushi, fukushi=remove_combi_fukushi)
    target_words = request.form.get('target-words')
    synonym = request.form.get('synonym')
    # エラーの有無判定
    error_dict = dict()
    # 入力データ
    if input_type == 'csv':
        if session.get('previous_file_name'):
            name = session.get('previous_file_name')
            file_name = session.get('previous_file_path')
        else:
            name, file_name, error_dict = get_csv_filename(request)
        used_category = 0
    else:
        # 利用者から送られてきた情報を基にデータ整理
        name, file_name = request.form.get('name').split('-')
        used_category = int(request.form.get('is_used_category'))
    name = name.replace(' ', '')
    # 送るデータの辞書
    sent_data_dict = dict(input_type=input_type, name=name, dimension=dimension, number=number,
                          hinshi=hinshi_jpn,
                          remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words,
                          is_used_category=used_category, synonym=synonym)
    # 品詞が1つも選択されなかった場合
    if not hinshi_eng:
        flash('品詞が選択されていません。', 'error')
        error_dict['hinshi'] = '品詞が選択されていません。'
    # 共起数が0以下だった場合
    if number < 1:
        flash('共起数が少なすぎます。', 'error')
        error_dict['number'] = '共起数が少なすぎます。'
    # sessionが切れている場合
    if request.form.get('has_previous') and not session.get('previous_file_name'):
        flash('セッション切れです。ファイルを再度アップロードしてください。', 'error')
    # errorがあれば
    if error_dict:
        sent_data_dict['error'] = error_dict
        return render_template('co_oc_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_data_dict)
    # 共起ネットワーク作成
    is_used_3d = True if dimension == 3 else False
    try:
        csv_file_name, co_oc_df, category_list = create_network(file_name=file_name, target_hinshi=hinshi_jpn, target_num=number,
                                                                remove_words=remove_words, remove_combi=remove_combi_dict,
                                                                target_words=target_words, input_type=input_type,
                                                                is_used_3d=is_used_3d, used_category=used_category, synonym=synonym)
        if is_used_3d:
            html_file_name = create_3d_network(co_oc_df, target_num=number,
                                               used_category=used_category, category_list=category_list)
        else:
            html_file_name = csv_file_name
    except:
        flash('ファイル形式が正しくありません。（入力形式に沿ってください）', 'error')
        sent_data_dict['error'] = dict(
            csv_file_invalid='ファイル形式が正しくありません。（入力形式に沿ってください）')
        return render_template('co_oc_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_data_dict)
    # sessionの登録
    if input_type == 'csv':
        session['previous_file_name'] = name
        session['previous_file_path'] = file_name
    session['file_name'] = csv_file_name
    session['dir_path'] = 'tmp'
    session['new_name'] = f'{name}_{"-".join(hinshi_jpn)}_{number}'
    # 利用者から送られてきた情報を基に送る情報を格納
    sent_data_dict['file_name'] = csv_file_name
    sent_data_dict['html_file_name'] = html_file_name
    sent_data_dict['co_oc_df'] = co_oc_df

    try:
        return render_template('co_oc_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_data_dict)
    except:
        return redirect(url_for('network.show'))
