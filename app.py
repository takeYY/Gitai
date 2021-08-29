from co_oc_3d_network import create_3d_network
from flask import Flask, flash, render_template, request, redirect, url_for, send_file, send_from_directory
from waitress import serve
from get_data import get_hinshi_dict, get_khcoder_df, get_basic_data, get_novels_tuple, get_edogawa_merge_df, dict_in_list2csv
from co_oc_network import create_network, get_csv_filename
from preprocessing import texts_preprocessing, get_other_option_dict, get_other_option_description_dict
from morphological import mrph_analysis, get_morphological_analysis_description_dict
import os

app = Flask(__name__)
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 16MBにデータ制限
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# SECRET_KEYを設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')


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
            name, file_name, error = get_csv_filename(app, request)
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


@app.route('/co-occurrence_network/visualization/<file_name>')
def show_co_oc_network(file_name):
    """
    共起ネットワーク用htmlファイル

    """
    return send_file(f'tmp/{file_name}.html')


@app.route('/co-oc_3D-network', methods=['GET', 'POST'])
def co_oc_3d_network():
    """
    3Dの共起ネットワーク

    """
    # 基本情報
    basic_data = get_basic_data(
        title='共起ネットワーク（3D）', active_url='co-oc_3d_network')
    # 江戸川乱歩作品関連の情報
    hinshi_dict = get_hinshi_dict()
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(),
                        name_file=get_novels_tuple(col1='name', col2='file_name'))

    if request.method == 'GET':
        return render_template('co-oc_3d_network.html', basic_data=basic_data, edogawa_data=edogawa_data)

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
        sent_error_data = dict(input_type=input_type, name=name, number=number, hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                               remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words, is_used_category=used_category)
        return render_template('co-oc_3d_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_error_data)
    # 共起ネットワーク作成
    try:
        csv_file_name, co_oc_df = create_network(file_name=file_name, target_hinshi=hinshi_jpn, target_num=number,
                                                 remove_words=remove_words, remove_combi=remove_combi_dict,
                                                 target_words=target_words, input_type=input_type,
                                                 is_used_3d=True, used_category=used_category)
        html_file_name = create_3d_network(
            co_oc_df, target_num=number, used_category=used_category)
    except:
        flash('ファイル形式が正しくありません。（入力形式に沿ってください）', 'error')
        sent_error_data = dict(input_type=input_type, name=name, number=number, hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                               remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words, is_used_category=used_category)
        return render_template('co-oc_3d_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_error_data)
    # 利用者から送られてきた情報を基に送る情報
    sent_data = dict(input_type=input_type, name=name, prev_csv_name=file_name, file_name=csv_file_name, html_file_name=html_file_name, number=number, hinshi=hinshi_jpn, hinshi_eng=hinshi_eng,
                     remove_words=remove_words, remove_combi=remove_combi_dict, target_words=target_words, co_oc_df=co_oc_df, is_used_category=used_category)

    try:
        return render_template('co-oc_3d_network.html', basic_data=basic_data, edogawa_data=edogawa_data, sent_data=sent_data)
    except:
        return redirect(url_for('co_oc_3d_network'))


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


@app.route('/morphological')
def morphological():
    """
    形態素解析

    """
    # 基本情報
    basic_data = get_basic_data(title='形態素解析', active_url='morph_analysis')
    # 形態素解析器の説明文
    description = get_morphological_analysis_description_dict()

    return render_template('morphological.html', basic_data=basic_data, mrph_type='None', description=description)


@app.route('/morphological/analysis', methods=['GET', 'POST'])
def morphological_analysis():
    """
    形態素解析の結果

    """
    # エラーなどでリダイレクトしたい場合
    if not request.method == 'POST':
        return redirect(url_for('morphological'))

    # 基本情報
    basic_data = get_basic_data(title='形態素解析', active_url='morph_analysis')
    # 形態素解析器の説明文
    description = get_morphological_analysis_description_dict()
    # 送信されたデータの取得と形態素解析器の種類
    text = request.form.get('words')
    mrph_type = request.form.get('mrph')
    # テキストが入力されなかった場合
    if not text:
        flash('テキストが入力されていません。', 'error')
        return render_template('morphological.html', basic_data=basic_data, mrph_type='None', description=description)
    # 形態素解析
    mrph_result, divide_dict = mrph_analysis(mrph_type, text)
    # 形態素解析の結果が返ってこなかった場合
    if not mrph_result:
        flash('解析に失敗しました。テキストデータが大きすぎます。', 'error')
        return render_template('morphological.html', basic_data=basic_data, mrph_type=mrph_type, description=description, mrph_data=dict(words=text))

    # mrph_resultをcsvとして保存し、df, csv_nameを取得
    result_df, csv_name = dict_in_list2csv(mrph_result, divide_dict)
    # 形態素解析結果をまとめるデータ群
    mrph_data = dict(words=text, result_df=result_df[:50], csv_name=csv_name,
                     over50=50 < len(result_df), columns_num=len(result_df.columns))

    return render_template('morphological.html', basic_data=basic_data, mrph_type=mrph_type, description=description, mrph_data=mrph_data)


@app.route('/preprocessing', methods=['GET', 'POST'])
def preprocessing():
    """
    テキストの前処理

    """
    # 基本情報
    basic_data = get_basic_data(
        title='テキストの前処理', active_url='preprocessing')
    # その他設定の項目取得
    other_option = get_other_option_dict()
    # その他設定の説明を{ other_option.value: description[i] }で取得
    other_option_description = get_other_option_description_dict()

    if request.method == 'GET':
        return render_template('preprocessing.html', basic_data=basic_data, other_option=other_option, description=other_option_description)
    else:
        # 利用者から送られてきた情報を取得
        texts = request.form.get('texts')
        # textsがない場合
        if not texts:
            flash('テキストが入力されていません。', 'error')
            return render_template('preprocessing.html', basic_data=basic_data, other_option=other_option, description=other_option_description)
        remove_words = request.form['remove-texts']
        remove_word_in_texts = request.form['remove-text-in-texts']
        replace_words = request.form['replace-texts']
        other_options = request.form.getlist('other-option')
        # 選択されたその他設定を取得
        selected_option = [other_option.get(k) for k in other_options]
        # 送られてきた情報を基にテキストを前処理
        preprocessed_text, errors = texts_preprocessing(
            texts, remove_words, remove_word_in_texts, replace_words, other_options)
        # エラーがある場合
        if errors:
            for error in errors:
                flash(error, 'error')
            sent_data = dict(texts=texts, remove_texts=remove_words, remove_text_in_texts=remove_word_in_texts,
                             other_option=selected_option, replace_texts=replace_words)
            return render_template('preprocessing.html', basic_data=basic_data, sent_data=sent_data, other_option=other_option, description=other_option_description)
        # 送るデータをまとめる
        sent_data = dict(texts=texts, remove_texts=remove_words, remove_text_in_texts=remove_word_in_texts,
                         other_option=selected_option, replace_texts=replace_words, preprocessed_texts=preprocessed_text)
        return render_template('preprocessing.html', basic_data=basic_data, sent_data=sent_data, other_option=other_option, description=other_option_description)


# おまじない
if __name__ == "__main__":
    serve(app)
