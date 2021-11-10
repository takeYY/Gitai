from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from get_data import get_basic_data, get_novels_tuple, get_category_list, get_co_oc_strength_dict, get_hinshi_dict
from co_oc_network import create_network, get_csv_filename
from co_oc_3d_network import create_3d_network
from morphological import get_morphological_analysis_description_dict
from aggregation import get_unique_hinshi_dict


network_page = Blueprint(
    'network', __name__, url_prefix='/rikkyo-edogawa/co-oc-network')


@network_page.route('/data-selection', methods=['GET'])
def data_selection():
    """
    共起ネットワーク
        データの選択画面

    """
    # 基本情報
    basic_data = get_basic_data(title='共起ネットワーク：データ選択',
                                active_url='co_oc_network')
    # 形態素解析器の説明文
    description = get_morphological_analysis_description_dict()
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(name_file=get_novels_tuple(col1='name',
                                                   col2='file_name'))
    # セッションをクリア
    session.clear()
    return render_template('co_oc_network/data_selection.html',
                           basic_data=basic_data,
                           edogawa_data=edogawa_data,
                           description=description)


@network_page.route('/options', methods=['POST'])
def options():
    """
    共起ネットワーク
        設定画面

    """
    # 基本情報
    basic_data = get_basic_data(title='共起ネットワーク：設定画面',
                                active_url='co_oc_network')
    # 形態素解析器の説明文
    description = get_morphological_analysis_description_dict()
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name',
                                                   col2='file_name'))
    # 入力データの形式
    input_type = request.form.get('input_type', session.get('input_type'))
    mrph_type = request.form.get('mrph') if input_type == 'edogawa' else ''
    # セッション切れの場合
    if not input_type:
        session.clear()
        flash('セッションが切れました。再度データを選択してください。', 'error')
        return render_template('co_oc_network/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data)
    # エラーの有無判定
    error_dict = dict()
    # 入力データ
    if input_type == 'csv':
        if session.get('input_name'):
            input_name = session.get('input_name')
            input_csv_name = session.get('input_csv_name')
        else:
            input_name, input_csv_name, error_dict = get_csv_filename(request)
            input_csv_name = input_csv_name.rsplit('.csv', 1)[0]
    else:
        # 利用者から送られてきた情報を基にデータ整理
        input_name, input_csv_name = request.form.get('name').split('-')
    input_name = input_name.replace(' ', '')
    # 品詞の辞書を取得
    hinshi_dict = get_unique_hinshi_dict(mrph_type, input_csv_name)
    # 品詞がない場合
    if not hinshi_dict:
        flash('品詞がありません。入力データの形式を確認してください。', 'error')
        error_dict['csv_file_invalid'] = '品詞がありません。入力データの形式を確認してください。'
        return render_template('co_oc_network/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               description=description,
                               sent_data=dict(error=error_dict))
    # 品詞の含有数でソート
    hinshi_dict = dict(sorted(hinshi_dict.items(), key=lambda x: x[1],
                       reverse=True))
    # errorがあれば
    if error_dict:
        return render_template('co_oc_network/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               error_data=error_dict)
    # カテゴリごとの表示有無
    is_used_category = request.form.get('is_used_category',
                                        session.get('is_used_category'))
    # カテゴリごとの表示を希望する場合
    if is_used_category == '1':
        category_list = get_category_list(input_csv_name)
    else:
        category_list = []
    # sessionの登録
    session['input_type'] = input_type
    session['input_name'] = input_name
    session['input_csv_name'] = input_csv_name
    session['is_used_category'] = is_used_category
    session['mrph_type'] = mrph_type
    if category_list and category_list[0] == '< 章なし >':
        session['has_category'] = 0
    else:
        session['has_category'] = 1
    # 入力データの取得
    input_data_dict = {'入力データタイプ': '江戸川乱歩作品' if input_type == 'edogawa' else 'CSVデータ',
                       '入力データ名': input_name,
                       '章ごとのカテゴリ分割': 'する' if is_used_category == '1' else 'しない',
                       '形態素解析器': 'MeCab' if input_type == 'edogawa' and mrph_type == 'mecab'
                       else 'Jumanpp' if input_type == 'edogawa' and mrph_type == 'juman' else ''}

    return render_template('co_oc_network/options.html',
                           basic_data=basic_data,
                           edogawa_data=edogawa_data,
                           category_list=category_list,
                           input_data=input_data_dict,
                           hinshi_dict=hinshi_dict)


@network_page.route('/result', methods=['POST'])
def result():
    """
    共起ネットワーク
        結果表示画面

    """
    # 基本情報
    basic_data = get_basic_data(title='共起ネットワーク：結果画面',
                                active_url='co_oc_network')
    # 形態素解析器の説明文
    description = get_morphological_analysis_description_dict()
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name', col2='file_name'))

    # 入力データの形式
    input_type = session.get('input_type')
    # セッション切れの場合
    if not input_type:
        session.clear()
        flash('セッションが切れました。再度データを選択してください。', 'error')
        return render_template('co_oc_network/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               description=description)
    # 利用者から送られてきた情報の取得
    name = session.get('input_name')
    file_name = session.get('input_csv_name')
    used_category = int(session.get('is_used_category'))
    mrph_type = session.get('mrph_type')
    dimension = int(request.form.get('dimension'))
    co_oc_strength = request.form.get('co_oc_strength')
    strength_max = float(request.form.get('strength_max'))
    number = int(request.form.get('number'))
    hinshi_jpn = request.form.getlist('hinshi')
    selected_category_list = request.form.getlist('category')
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
    name = name.replace(' ', '')
    # 送るデータの辞書
    sent_data_dict = dict(input_type=input_type, name=name, dimension=dimension, number=number,
                          hinshi=hinshi_jpn, category=selected_category_list,
                          remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words,
                          is_used_category=used_category, synonym=synonym, co_oc_strength=co_oc_strength, strength_max=strength_max)
    # 品詞が1つも選択されなかった場合
    if not hinshi_jpn:
        flash('品詞が選択されていません。', 'error')
        error_dict['hinshi'] = '品詞が選択されていません。'
    # 共起数が0以下だった場合
    if number < 1:
        flash('共起数が少なすぎます。', 'error')
        error_dict['number'] = '共起数が少なすぎます。'
    # edogawa選択、カテゴリごとの表示選択、章がある作品において、チェックが一つもなかった場合
    if input_type == 'edogawa' and used_category and int(session.get('has_category')) and not selected_category_list:
        flash('カテゴリが選択されていません。', 'error')
        error_dict['category'] = 'カテゴリが選択されていません。'
    # 品詞の辞書を取得
    hinshi_dict = get_unique_hinshi_dict(mrph_type, file_name)
    # errorがあれば
    if error_dict:
        sent_data_dict['error'] = error_dict
        return render_template('co_oc_network/options.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               sent_data=sent_data_dict,
                               category_list=get_category_list(file_name),
                               hinshi_dict=hinshi_dict)
    # 共起ネットワーク作成
    is_used_3d = True if dimension == 3 else False
    # 共起強度の対象を設定
    target_coef = get_co_oc_strength_dict().get(co_oc_strength, '共起回数')
    try:
        csv_file_name, co_oc_df, category_list = create_network(file_name=file_name, target_hinshi=hinshi_jpn, target_num=number,
                                                                remove_words=remove_words, remove_combi=remove_combi_dict,
                                                                target_words=target_words, input_type=input_type,
                                                                is_used_3d=is_used_3d, used_category=used_category, synonym=synonym,
                                                                selected_category=selected_category_list,
                                                                target_coef=target_coef,
                                                                strength_max=strength_max, mrph_type=mrph_type)
        if is_used_3d:
            html_file_name = create_3d_network(co_oc_df, target_num=number,
                                               used_category=used_category, category_list=category_list,
                                               target_coef=target_coef)
        else:
            html_file_name = csv_file_name
    except:
        import traceback
        traceback.print_exc()
        flash('ファイル形式が正しくありません。（入力形式に沿ってください）', 'error')
        sent_data_dict['error'] = dict(
            csv_file_invalid='ファイル形式が正しくありません。（入力形式に沿ってください）')
        return render_template('co_oc_network/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               sent_data=sent_data_dict,
                               description=description)
    # csvダウンロード設定
    dl_data = dict(file_name=csv_file_name,
                   dl_type='result',
                   new_name=f'{name}_{"-".join(hinshi_jpn)}_{number}')
    # 利用者から送られてきた情報を基に送る情報を格納
    sent_data_dict['file_name'] = csv_file_name
    sent_data_dict['html_file_name'] = html_file_name
    sent_data_dict['co_oc_df'] = co_oc_df
    # 入力データの取得
    input_data_dict = {'入力データタイプ': '江戸川乱歩作品' if input_type == 'edogawa' else 'CSVデータ',
                       '入力データ名': name,
                       '章ごとのカテゴリ分割': 'する' if used_category == '1' else 'しない',
                       '形態素解析器': 'MeCab' if input_type == 'edogawa' and mrph_type == 'mecab'
                       else 'Jumanpp' if input_type == 'edogawa' and mrph_type == 'juman' else ''}
    # 設定データの取得
    options_dict = {'表示形式': '2D' if dimension == 2 else '3D',
                    '共起数上位': number,
                    '共起強度': target_coef,
                    '共起強度の最大値': strength_max,
                    '可視化対象の品詞': ', '.join(hinshi_jpn),
                    'カテゴリー選択（3Dのみ）': ', '.join(selected_category_list) if selected_category_list else '',
                    '指定ワード': ', '.join(target_words.split('\r\n')),
                    '同義語指定': synonym,
                    '除去ワード': ', '.join(remove_words),
                    '除去対象の品詞組み合わせ（名詞）': ', '.join(remove_combi_meishi),
                    '除去対象の品詞組み合わせ（動詞）': ', '.join(remove_combi_doushi),
                    '除去対象の品詞組み合わせ（形容詞）': ', '.join(remove_combi_keiyoushi),
                    '除去対象の品詞組み合わせ（副詞）': ', '.join(remove_combi_fukushi)}

    try:
        return render_template('co_oc_network/result.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               sent_data=sent_data_dict,
                               input_data=input_data_dict,
                               options=options_dict,
                               dl_data=dl_data)
    except:
        return redirect(url_for('network.data_selection'))
