from os import error
from flask import Blueprint, render_template, request, session, flash
from aggregation import create_aggregation, valid_agg_columns, get_unique_hinshi_dict
from get_data import get_basic_data, get_novels_tuple, get_hinshi_dict
from morphological import get_morphological_analysis_description_dict
from co_oc_network import get_csv_filename

aggregation_page = Blueprint(
    'aggregation', __name__, url_prefix='/rikkyo-edogawa/aggregation')


@aggregation_page.route('data-selection', methods=['GET'])
def data_selection():
    """
    データの集計
      データの選択画面

    """
    # 基本情報
    basic_data = get_basic_data(title='データの集計', active_url='aggregation')
    # 形態素解析器の説明文
    description = get_morphological_analysis_description_dict()
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(name_file=get_novels_tuple(col1='name',
                                                   col2='file_name'))
    session.clear()
    return render_template('aggregation/data_selection.html',
                           basic_data=basic_data,
                           edogawa_data=edogawa_data,
                           description=description)


@aggregation_page.route('options', methods=['POST'])
def options():
    """
    データの集計
      設定画面

    """
    # 基本情報
    basic_data = get_basic_data(title='データの集計', active_url='aggregation')
    # 形態素解析器の説明文
    description = get_morphological_analysis_description_dict()
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name',
                                                   col2='file_name'))
    # エラーの有無判定
    error_dict = dict()
    # 利用者から送られてきた情報を基にデータ整理
    input_type = request.form.get('input_type', session.get('input_type'))
    mrph_type = request.form.get('mrph') if input_type == 'edogawa' else ''
    # セッション切れの場合
    if not input_type:
        session.clear()
        flash('セッションが切れました。再度データを選択してください。', 'error')
        return render_template('aggregation/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               description=description)
    if input_type == 'csv':
        if session.get('input_name'):
            input_name = session.get('input_name')
            input_csv_name = session.get('input_csv_name')
        else:
            input_name, input_csv_name, error_dict = get_csv_filename(request)
            input_csv_name = input_csv_name.rsplit('.csv', 1)[0]
        # エラーチェック
        if error_dict:
            return render_template('aggregation/data_selection.html',
                                   basic_data=basic_data,
                                   edogawa_data=edogawa_data,
                                   description=description,
                                   sent_data=dict(error=error_dict))
        # 入力CSVの列名チェック
        if not valid_agg_columns(input_csv_name):
            flash('集計に必要なデータがありません。', 'error')
            error_dict['csv_file_invalid'] = '集計に必要なデータがありません。'
            return render_template('aggregation/data_selection.html',
                                   basic_data=basic_data,
                                   edogawa_data=edogawa_data,
                                   description=description,
                                   sent_data=dict(error=error_dict))
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
        return render_template('aggregation/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               description=description,
                               sent_data=dict(error=error_dict))
    # 品詞の含有数でソート
    hinshi_dict = dict(sorted(hinshi_dict.items(), key=lambda x: x[1],
                       reverse=True))
    # sessionの登録
    session['input_type'] = input_type
    session['input_name'] = input_name
    session['input_csv_name'] = input_csv_name
    session['mrph_type'] = mrph_type
    # 入力データの取得
    input_data_dict = {'入力データタイプ': '江戸川乱歩作品' if input_type == 'edogawa' else 'CSVデータ',
                       '入力データ名': input_name,
                       '形態素解析器': 'MeCab' if input_type == 'edogawa' and mrph_type == 'mecab'
                       else 'Jumanpp' if input_type == 'edogawa' and mrph_type == 'juman' else ''}

    return render_template('aggregation/options.html',
                           basic_data=basic_data,
                           edogawa_data=edogawa_data,
                           input_data=input_data_dict,
                           hinshi_dict=hinshi_dict)


@aggregation_page.route('result', methods=['POST'])
def result():
    """
    データの集計

    """
    # 基本情報
    basic_data = get_basic_data(title='データの集計', active_url='aggregation')
    # 形態素解析器の説明文
    description = get_morphological_analysis_description_dict()
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name',
                                                   col2='file_name'))
    # session情報を取得
    input_type = session.get('input_type')
    input_name = session.get('input_name')
    input_csv_name = session.get('input_csv_name')
    mrph_type = session.get('mrph_type')
    # セッション切れの場合
    if not input_type:
        session.clear()
        flash('セッションが切れました。再度データを選択してください。', 'error')
        return render_template('aggregation/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               description=description)
    # エラーの有無判定
    error_dict = dict()
    # 入力データの取得
    input_data_dict = {'入力データタイプ': '江戸川乱歩作品' if input_type == 'edogawa' else 'CSVデータ',
                       '入力データ名': input_name,
                       '形態素解析器': 'MeCab' if input_type == 'edogawa' and mrph_type == 'mecab'
                       else 'Jumanpp' if input_type == 'edogawa' and mrph_type == 'juman' else ''}
    # 設定項目の取得
    hinshi_jpn = request.form.getlist('hinshi')
    # 品詞の辞書を取得
    hinshi_dict = get_unique_hinshi_dict(mrph_type, input_csv_name)
    # 品詞の含有数でソート
    hinshi_dict = dict(sorted(hinshi_dict.items(), key=lambda x: x[1],
                       reverse=True))
    # 品詞が1つも選択されていない場合
    if not hinshi_jpn:
        flash('品詞が選択されていません。')
        error_dict['hinshi'] = '品詞が選択されていません。'
        return render_template('aggregation/options.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               input_data=input_data_dict,
                               hinshi_dict=hinshi_dict,
                               sent_data=dict(error=error_dict))
    # データの集計処理
    try:
        result_df, file_name = create_aggregation(mrph_type,
                                                  input_csv_name,
                                                  target_hinshi=hinshi_jpn)
    except:
        flash('ファイル形式が正しくありません。（入力形式に沿ってください）', 'error')
        error_dict['csv_file_invalid'] = 'ファイル形式が正しくありません。（入力形式に沿ってください）'
        return render_template('aggregation/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               description=description,
                               sent_data=dict(error=error_dict))
    sent_data = dict(name=input_name, file_name=file_name,
                     df=result_df, hinshi=hinshi_jpn)
    # csvダウンロード設定
    dl_data = dict(file_name=file_name,
                   dl_type='result',
                   new_name=f'{input_name}の集計結果')
    # 設定の取得
    options_dict = {'可視化対象の品詞': ', '.join(hinshi_jpn)}
    try:
        return render_template('aggregation/result.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               description=description,
                               sent_data=sent_data,
                               input_data=input_data_dict,
                               options=options_dict,
                               dl_data=dl_data)
    except:
        return render_template('aggregation/data_selection.html',
                               basic_data=basic_data,
                               edogawa_data=edogawa_data,
                               description=description)
