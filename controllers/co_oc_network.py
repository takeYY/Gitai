from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from get_data import get_basic_data, get_novels_tuple, get_hinshi_dict
from co_oc_network import create_network
from co_oc_3d_network import create_3d_network
from morphological import get_morphological_analysis_description_dict
from models.co_oc_network.input import InputCoOcNetwork
from models.co_oc_network.option import OptionCoOcNetwork


network_page = Blueprint(
    'network', __name__, url_prefix='/rikkyo-edogawa/co-oc-network')


def render_data_selection(basic_data, edogawa_data, description, input_data=None):
    return render_template('co_oc_network/data_selection.html',
                           basic_data=basic_data,
                           edogawa_data=edogawa_data,
                           description=description,
                           input_data=input_data)


def render_options(basic_data, edogawa_data, input_data, option=None):
    return render_template('co_oc_network/options.html',
                           basic_data=basic_data,
                           edogawa_data=edogawa_data,
                           category_list=input_data.category_list,
                           input_table=input_data.get_table_dict(),
                           hinshi_dict=input_data.hinshi,
                           option=option)


def render_result(basic_data, result_data, dl_data, input_data, option):
    return render_template('co_oc_network/result.html',
                           basic_data=basic_data,
                           result_data=result_data,
                           dl_data=dl_data,
                           input_table=input_data.get_table_dict(),
                           option_table=option.get_table_dict())


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
    return render_data_selection(basic_data, edogawa_data, description)


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
    # 入力データの設定
    input_data = InputCoOcNetwork(request, session)
    # セッション切れの場合
    if not input_data.data_type:
        session.clear()
        flash('セッションが切れました。再度データを選択してください。', 'error')
        return render_data_selection(basic_data, edogawa_data, description)
    # errorがあれば
    if input_data.__dict__.get('errors'):
        return render_data_selection(basic_data, edogawa_data, description,
                                     input_data=input_data.__dict__)
    # 品詞がない場合
    if not input_data.hinshi:
        flash('品詞がありません。入力データの形式を確認してください。', 'error')
        input_data.set_errors('csv_file_invalid',
                              '品詞がありません。入力データの形式を確認してください。')
        return render_data_selection(basic_data, edogawa_data, description,
                                     input_data=input_data.__dict__)
    # 品詞の含有数でソート
    input_data.hinshi_sort()
    # sessionの登録
    session['data_type'] = input_data.data_type
    session['input_name'] = input_data.name
    session['input_csv_name'] = input_data.csv_name
    session['is_used_category'] = input_data.is_used_category
    session['mrph_type'] = input_data.mrph_type
    session['has_category'] = input_data.has_category_list()

    return render_options(basic_data, edogawa_data, input_data)


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
    input_data = InputCoOcNetwork(request, session)
    # セッション切れの場合
    if not input_data.data_type:
        session.clear()
        flash('セッションが切れました。再度データを選択してください。', 'error')
        return render_data_selection(basic_data, edogawa_data, description)
    # 利用者から送られてきた情報の取得
    option = OptionCoOcNetwork(request)
    # 品詞が1つも選択されなかった場合
    if not option.hinshi_jpn:
        flash('品詞が選択されていません。', 'error')
        option.set_errors('hinshi', '品詞が選択されていません。')
    # 共起数が0以下だった場合
    if option.number < 1:
        flash('共起数が少なすぎます。', 'error')
        option.set_errors('number', '共起数が少なすぎます。')
    # edogawa選択、カテゴリごとの表示選択、章がある作品において、チェックが一つもなかった場合
    if input_data.data_type == 'edogawa' and input_data.is_used_category and int(session.get('has_category')) and not option.selected_category:
        flash('カテゴリが選択されていません。', 'error')
        option.set_errors('category', 'カテゴリが選択されていません。')
    # errorがあれば
    if option.__dict__.get('errors'):
        return render_options(basic_data, edogawa_data, input_data,
                              option=option.__dict__)
    # 共起ネットワーク作成
    try:
        csv_file_name, co_oc_df = create_network(file_name=input_data.csv_name, target_hinshi=option.hinshi_jpn, target_num=option.number,
                                                 remove_words=option.remove_words, remove_combi=option.remove_combi,
                                                 target_words=option.target_words, data_type=input_data.data_type,
                                                 is_used_3d=option.is_3d, used_category=input_data.is_used_category, synonym=option.synonym,
                                                 selected_category=option.selected_category,
                                                 target_coef=option.target_coef,
                                                 strength_max=option.strength_max, mrph_type=input_data.mrph_type)
        if option.is_3d:
            html_file_name = create_3d_network(co_oc_df, target_num=option.number,
                                               used_category=input_data.is_used_category, category_list=option.selected_category,
                                               target_coef=option.target_coef)
        else:
            html_file_name = csv_file_name
    except:
        import traceback
        traceback.print_exc()
        flash('ファイル形式が正しくありません。（入力形式に沿ってください）', 'error')
        input_data.set_errors('csv_file_invalid',
                              'ファイル形式が正しくありません。（入力形式に沿ってください）')
        return render_data_selection(basic_data, edogawa_data, description,
                                     input_data=input_data.__dict__)
    # csvダウンロード設定
    dl_data = dict(file_name=csv_file_name,
                   dl_type='result',
                   new_name=f'{input_data.name}_{"-".join(option.hinshi_jpn)}_{option.number}')
    # 結果情報を格納
    result_data = dict(file_name=csv_file_name,
                       html_file_name=html_file_name,
                       co_oc_df=co_oc_df[:option.number])

    try:
        return render_result(basic_data, result_data, dl_data,
                             input_data, option)
    except:
        return redirect(url_for('network.data_selection'))
