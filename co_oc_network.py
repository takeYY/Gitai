from flask import flash
import pandas as pd
import itertools
import collections
import datetime
from werkzeug.utils import secure_filename
from get_data import get_jumanpp_df, get_datetime_now
import os

ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS')


# 拡張子の制限
def allowed_csv_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# csvファイルのバリデーション
def csv_file_invalid(request):
    if 'file' not in request.files:
        flash('ファイルが存在しません。', 'error')
        return True
    file = request.files['file']
    if file.filename == '':
        flash('ファイルが選択されていません。', 'error')
        return True
    if not allowed_csv_file(file.filename):
        flash('ファイル形式がcsvではありません。', 'error')
        return True

    return False


def get_csv_filename(app, request):
    if csv_file_invalid(request):
        return '', True

    file = request.files['file']
    filename = get_datetime_now() + '_input_' + secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    return filename, False


# ネットワーク描画のメイン処理定義
def kyoki_word_network(target_num=250, file_name='3742_9_3_11_02'):
    from pyvis.network import Network

    # got_net = Network(height="1000px", width="95%", bgcolor="#222222", font_color="white", notebook=True)
    got_net = Network(height="100%", width="100%",
                      bgcolor="#222222", font_color="white")
    # got_net = Network(height="1000px", width="95%", bgcolor="#FFFFFF", font_color="black", notebook=True)

    # set the physics layout of the network
    # got_net.barnes_hut()
    got_net.force_atlas_2based()
    got_data = pd.read_csv(f'tmp/{file_name}.csv')[:target_num]

    sources = got_data['first']  # count
    targets = got_data['second']  # first
    weights = got_data['count']  # second

    edge_data = zip(sources, targets, weights)

    for i, e in enumerate(edge_data):
        src = e[0]
        dst = e[1]
        w = e[2]

        got_net.add_node(src, src, title=src, group=i)
        got_net.add_node(dst, dst, title=dst, group=i)
        got_net.add_edge(src, dst, value=w)

    neighbor_map = got_net.get_adj_list()

    # add neighbor data to node hover data
    for node in got_net.nodes:
        node["title"] += " Neighbors:<br>" + \
            "<br>".join(neighbor_map[node["id"]])
        node["value"] = len(neighbor_map[node["id"]])

    return got_net


def create_network(file_name='kaijin_nijumenso', target_hinshi=['名詞'], target_num=250, remove_words='', target_words='', input_type='edogawa'):
    """
    共起ネットワークの作成

    params
    ------
    file_name: str, default='kaijin_nijumenso'
        作品のファイル名

    target_hinshi: list, default=['名詞']
        共起に含めたい品詞

    target_num: int, default=250
        表示したい上位共起数

    remove_words: str, default=''
        共起に含めたくない除去ワード集

    target_words: str, default=''
        指定した単語の共起のみ表示する

    """
    if input_type == 'edogawa':
        # jumanppにより形態素解析したDF取得
        df = get_jumanpp_df(file_name)
    else:
        df = pd.read_csv(f'tmp/{file_name}')
    # 除去ワードリスト
    remove_words_list = remove_words.split('\r\n')

    # 形態素解析DFから各列の要素をリストで取得
    try:
        # Jumanppによる形態素解析の場合
        midashi = list(df['見出し'])
    except:
        # Mecabによる形態素解析の場合
        midashi = list(df['表層形'])
    try:
        genkei = list(df['原型'])
    except:
        genkei = list(df['原形'])
    hinshi = list(df['品詞'])
    sentences = []
    for i in range(len(midashi)):
        sentences.append([midashi[i], genkei[i], hinshi[i]])

    # 同一文の中で設定に合致したwordsをkeywordsに含める
    keywords = []
    words = []
    for sentence in sentences:
        # 句点があれば
        if sentence[0] == '。':
            keywords.append(words)
            words = []
            continue

        # 品詞がtarget_hinshiに含まれている and not (見出しが除去ワードリストに入っている or 原型が除去ワードリストに入っている)
        if sentence[2] in target_hinshi and not (sentence[0] in remove_words_list or sentence[1] in remove_words_list):
            words.append(sentence[1])

    # keywordsを基にカウントベースで共起をカウント
    sentence_combinations = [list(itertools.combinations(
        set(sentence), 2)) for sentence in keywords]
    sentence_combinations = [[tuple(sorted(words)) for words in sentence]
                             for sentence in sentence_combinations]
    target_combinations = []
    for sentence in sentence_combinations:
        target_combinations.extend(sentence)
    ct = collections.Counter(target_combinations)

    # 指定ワードが含まれるレコードのみ抽出
    cols = [{'first': i[0][0], 'second': i[0][1], 'count': i[1]}
            for i in ct.most_common()]
    co_oc_df = pd.DataFrame(cols)
    if target_words:
        new_co_oc_df = pd.DataFrame()
        for tw in target_words.split('\r\n'):
            new_co_oc_df = pd.concat(
                [new_co_oc_df, co_oc_df.query(' @tw in first or @tw in second ')])
        co_oc_df = new_co_oc_df.sort_values('count', ascending=False).drop_duplicates(
            subset=['first', 'second']).reset_index(drop=True)
    # 所定の構造でCSVファイルに出力
    now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    co_oc_df.to_csv(f'tmp/{now}.csv', index=False, encoding='utf_8_sig')

    try:
        # 処理の実行
        got_net = kyoki_word_network(target_num=target_num, file_name=now)
        got_net.write_html(f'tmp/{now}.html')
        return now, co_oc_df
    except:
        return '', ''
