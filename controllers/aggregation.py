from os import error
from flask import Blueprint, render_template, request, session, flash, redirect, url_for
from src.aggregation import create_aggregation, valid_agg_columns
from src.description import csv_file_description, morphological_analysis_description
from src.get_data import get_basic_data, get_novels_tuple, get_hinshi_dict
from models.aggregation.option import OptionAggregation
from models.aggregation.input import InputAggregation


aggregation_page = Blueprint(
    'aggregation', __name__, url_prefix='/rikkyo-edogawa/aggregation')


def render_data_selection(basic_data: dict, edogawa_data: dict, description: dict, input_data: dict = None):
    return render_template('aggregation/data_selection.html',
                           basic_data=basic_data,
                           edogawa_data=edogawa_data,
                           description=description,
                           input_data=input_data)


def render_options(basic_data: dict, input_data: InputAggregation, option: dict = None):
    return render_template('aggregation/options.html',
                           basic_data=basic_data,
                           input_table=input_data.get_table_dict(),
                           hinshi_dict=input_data.hinshi,
                           option=option)


def render_result(basic_data: dict, result_data: dict, dl_data: dict, input_table: dict, option_table: dict):
    return render_template('aggregation/result.html',
                           basic_data=basic_data,
                           result_data=result_data,
                           dl_data=dl_data,
                           input_table=input_table,
                           option_table=option_table)


@aggregation_page.route('data-selection', methods=['GET'])
def data_selection():
    """
    データの集計
      データの選択画面

    """
    # 基本情報
    basic_data = get_basic_data(title='データの集計', active_url='aggregation')
    # 形態素解析器の説明文
    description = dict(mrph=morphological_analysis_description(),
                       csv_sample=csv_file_description())
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(name_file=get_novels_tuple(col1='name',
                                                   col2='file_name'))
    session.clear()
    return render_data_selection(basic_data, edogawa_data, description)


@aggregation_page.route('options', methods=['POST'])
def options():
    """
    データの集計
      設定画面

    """
    # 基本情報
    basic_data = get_basic_data(title='データの集計', active_url='aggregation')
    # 形態素解析器の説明文
    description = dict(mrph=morphological_analysis_description(),
                       csv_sample=csv_file_description())
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name',
                                                   col2='file_name'))
    # 入力データの設定
    input_data = InputAggregation(request, session)
    # セッション切れの場合
    if not input_data.data_type:
        session.clear()
        flash('セッションが切れました。再度データを選択してください。', 'error')
        return render_data_selection(basic_data, edogawa_data, description)
    # errorがあれば
    if input_data.__dict__.get('errors'):
        return render_data_selection(basic_data, edogawa_data, description,
                                     input_data=input_data.__dict__)
    # 入力CSVの列名チェック
    if input_data.data_type == 'csv' and not valid_agg_columns(input_data.csv_name):
        flash('集計に必要なデータがありません。', 'error')
        input_data.set_errors('csv_file_invalid', '集計に必要なデータがありません。')
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
    session['mrph_type'] = input_data.mrph_type

    return render_options(basic_data, input_data)


@aggregation_page.route('result', methods=['POST'])
def result():
    """
    データの集計

    """
    # 基本情報
    basic_data = get_basic_data(title='データの集計', active_url='aggregation')
    # 形態素解析器の説明文
    description = dict(mrph=morphological_analysis_description(),
                       csv_sample=csv_file_description())
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name',
                                                   col2='file_name'))
    # 入力データの形式
    input_data = InputAggregation(request, session)
    # セッション切れの場合
    if not input_data.data_type:
        session.clear()
        flash('セッションが切れました。再度データを選択してください。', 'error')
        return render_data_selection(basic_data, edogawa_data, description)
    # 利用者から送られてきた情報の取得
    option = OptionAggregation(request)
    # 品詞の含有数でソート
    input_data.hinshi_sort()
    # 品詞が1つも選択されていない場合
    if not option.hinshi_jpn:
        flash('品詞が選択されていません。', 'error')
        option.set_errors('hinshi', '品詞が選択されていません。')
        return render_options(basic_data, input_data,
                              option=option.__dict__)
    # データの集計処理
    try:
        result_df, file_name = create_aggregation(input_data.mrph_type,
                                                  input_data.csv_name,
                                                  target_hinshi=option.hinshi_jpn)
    except:
        flash('ファイル形式が正しくありません。（入力形式に沿ってください）', 'error')
        input_data.set_errors('csv_file_invalid',
                              'ファイル形式が正しくありません。（入力形式に沿ってください）')
        return render_data_selection(basic_data, edogawa_data, description,
                                     input_data=input_data.__dict__)
    # csvダウンロード設定
    dl_data = dict(file_name=file_name,
                   dl_type='result',
                   new_name=f'{input_data.name}の集計結果')
    # 結果情報を格納
    result_data = dict(file_name=file_name,
                       html_file_name=file_name,
                       df=result_df[:51])
    try:
        return render_result(basic_data, result_data, dl_data,
                             input_data.get_table_dict(), option.get_table_dict())
    except:
        return redirect(url_for('aggregation.data_selection'))
