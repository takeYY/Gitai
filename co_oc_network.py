from flask import flash
import pandas as pd
import itertools
import collections
import datetime
from werkzeug.utils import secure_filename
from get_data import get_jumanpp_df, get_mecab_with_category_df, get_datetime_now, get_hinshi_dict
import os

ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')


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


# 選択された品詞である or 除去ワードリストにない単語であるか判定
def can_add_genkei2words(sentence, target_hinshi, remove_words_list):
    midashi = sentence[0]
    genkei = sentence[1]
    hinshi = sentence[2]

    # 品詞が可視化対象の品詞に含まれていない場合
    if not hinshi in target_hinshi:
        return False
    # 見出し や 原形が除去ワードリストに含まれている場合
    if midashi in remove_words_list or genkei in remove_words_list:
        return False

    return True


# 除去対象の品詞組み合わせであるか判定
def has_not_remove_combinations(word1, word2, remove_dict, hinshi_dict):
    has_combi = False
    # 各品詞に対して、それぞれ2番目の品詞との組み合わせであるか判定
    for key, value in hinshi_dict.items():
        # 1番目の品詞が指定されていない時
        if not remove_dict.get(key):
            continue

        # 1番目の品詞と2番目の品詞が合致した場合
        if word1[1] in value and word2[1] in remove_dict.get(key):
            has_combi = True
            break
    if has_combi:
        return False

    # 除去対象の品詞組み合わせの何にも合致しなかった場合
    return True


def get_csv_filename(request):
    if csv_file_invalid(request):
        return '', '', True

    file = request.files['file']
    filename = file.filename
    save_filename = get_datetime_now() + '_input_' + secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, save_filename))

    return filename, save_filename, False


def modify_df_with_synonym(df, synonym):
    # key:置換対象の文字列, value:置換後の文字列
    synonym_dict = {}
    synonym_items = [s for s in synonym.split('・') if s != '']
    for item in synonym_items:
        item_split = [s for s in item.split('\r\n') if s != '']
        replace_word = item_split[0]
        target_word = item_split[1]
        for tw in target_word.split(','):
            synonym_dict[tw] = replace_word

    # 同義語設定
    if '原形' in df.columns:
        df_match = df.query(' 原形 in @synonym_dict.keys() ', engine='python')
        df_unmatch = df.query(
            ' 原形 not in @synonym_dict.keys() ', engine='python')
        # 同義語に指定された単語を置き換え
        df_match = df_match.replace({'原形': synonym_dict})
    else:
        df_match = df.query(' 原型 in @synonym_dict.keys() ', engine='python')
        df_unmatch = df.query(
            ' 原型 not in @synonym_dict.keys() ', engine='python')
        # 同義語に指定された単語を置き換え
        df_match = df_match.replace({'原型': synonym_dict})
    # 品詞を固有名詞に設定
    df_match['品詞'] = '固有名詞'
    # 結合
    df = pd.concat([df_match, df_unmatch]).sort_index()

    return df


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


def create_network(file_name='kaijin_nijumenso', target_hinshi=['名詞'], target_num=250, remove_words='', remove_combi='', target_words='', input_type='edogawa', is_used_3d=False, used_category=0, synonym=''):
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

    remove_combi: dict, default=''
        除去対象の品詞組み合わせ

    target_words: str, default=''
        指定した単語の共起のみ表示する

    """
    if input_type == 'edogawa':
        if used_category == 0 or not is_used_3d:
            # jumanppにより形態素解析したDF取得
            df = get_jumanpp_df(file_name)
        else:
            # MeCabにより形態素解析されたDF取得
            df = get_mecab_with_category_df(file_name)
    else:
        df = pd.read_csv(f'tmp/{file_name}')
    # 除去ワードリスト
    remove_words_list = remove_words.split('\r\n')

    # 同義語設定
    if synonym:
        df = modify_df_with_synonym(df, synonym)
        target_hinshi.append('固有名詞')

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
    if used_category == 0 or not is_used_3d:
        for i in range(len(midashi)):
            sentences.append([midashi[i], genkei[i], hinshi[i]])
    else:
        category = list(df['カテゴリー'])
        for i in range(len(midashi)):
            sentences.append([midashi[i], genkei[i], hinshi[i], category[i]])
    # 品詞の辞書を取得
    hinshi_dict = get_hinshi_dict()
    # 感動詞の削除
    del hinshi_dict['kandoushi']
    for key in remove_combi.keys():
        if not remove_combi.get(key):
            del hinshi_dict[key]

    # 同一文の中で設定に合致したwordsをkeywordsに含める
    keywords = []
    words = []
    for sentence in sentences:
        # 句点があれば
        if sentence[0] == '。':
            keywords.append(words)
            words = []
            continue

        if used_category == 1 and is_used_3d:
            # 品詞がtarget_hinshiに含まれている and not (見出しが除去ワードリストに入っている or 原型が除去ワードリストに入っている)
            if can_add_genkei2words(sentence, target_hinshi, remove_words_list):
                words.append((sentence[1], sentence[2], sentence[3]))
        else:
            # 品詞がtarget_hinshiに含まれている and not (見出しが除去ワードリストに入っている or 原型が除去ワードリストに入っている)
            if can_add_genkei2words(sentence, target_hinshi, remove_words_list):
                words.append((sentence[1], sentence[2]))

    # keywordsを基に単語の全組み合わせ作成
    sentence_combinations = [list(itertools.combinations(
        set(sentence), 2)) for sentence in keywords]
    sentence_combinations = [[tuple(sorted(words)) for words in sentence]
                             for sentence in sentence_combinations]
    if hinshi_dict:
        # 除去対象の品詞組み合わせを削除
        new_sentence_combinations = []
        for sc in sentence_combinations:
            combination_list = []
            for word1, word2 in sc:
                if has_not_remove_combinations(word1, word2, remove_combi, hinshi_dict):
                    combination_list.append((word1, word2))
            new_sentence_combinations.append(combination_list)
        sentence_combinations = new_sentence_combinations
    # keywordsを基にカウントベースで共起数をカウント
    target_combinations = []
    for sentence in sentence_combinations:
        target_combinations.extend(sentence)
    ct = collections.Counter(target_combinations)
    if used_category == 1 and is_used_3d:
        cols = [{'first': i[0][0][0], 'first_type': i[0][0][1],
                 'second': i[0][1][0], 'second_type': i[0][1][1], 'count': i[1], 'カテゴリー': i[0][0][2]}
                for i in ct.most_common()]
    else:
        cols = [{'first': i[0][0][0], 'first_type': i[0][0][1],
                 'second': i[0][1][0], 'second_type': i[0][1][1], 'count': i[1]}
                for i in ct.most_common()]
    co_oc_df = pd.DataFrame(cols)
    # 指定ワードが含まれるレコードのみ抽出
    if target_words:
        new_co_oc_df = pd.DataFrame()
        for tw in target_words.split('\r\n'):
            new_co_oc_df = pd.concat(
                [new_co_oc_df, co_oc_df.query(' @tw in first or @tw in second ')])
        co_oc_df = new_co_oc_df.sort_values('count', ascending=False).drop_duplicates(
            subset=['first', 'second']).reset_index(drop=True)
    # 所定の構造でCSVファイルに出力
    now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S%f')
    co_oc_df.to_csv(f'tmp/{now}.csv', index=False, encoding='utf_8_sig')

    try:
        # 2Dの共起ネットワークHTML作成
        if not is_used_3d:
            got_net = kyoki_word_network(target_num=target_num, file_name=now)
            got_net.write_html(f'tmp/{now}.html')
        return now, co_oc_df
    except:
        return '', ''
