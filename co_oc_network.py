from flask import flash
import math
import pandas as pd
import numpy as np
import itertools
import collections
from werkzeug.utils import secure_filename
from get_data import get_jumanpp_df, get_mecab_with_category_df, get_datetime_now, get_hinshi_dict, create_random_string
import os

ALLOWED_EXTENSIONS = os.environ.get('ALLOWED_EXTENSIONS')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')


# 拡張子の制限
def allowed_csv_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# csvファイルのバリデーション
def get_csv_error_message(request):
    if 'file' not in request.files:
        error_message = 'ファイルが存在しません。'
        flash(error_message, 'error')
        return error_message
    file = request.files['file']
    if file.filename == '':
        error_message = 'ファイルが選択されていません。'
        flash(error_message, 'error')
        return error_message
    if not allowed_csv_file(file.filename):
        error_message = 'ファイル形式がcsvではありません。'
        flash(error_message, 'error')
        return error_message

    return ''


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
    error_message = get_csv_error_message(request)
    if error_message:
        return '', '', dict(csv_file_invalid=error_message)

    file = request.files['file']
    input_filename = file.filename
    csv_filename = get_datetime_now() + '_input_' + secure_filename(input_filename)
    file.save(os.path.join(UPLOAD_FOLDER, csv_filename))

    return input_filename, csv_filename, dict()


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
    df_match = df.query(' 原形 in @synonym_dict.keys() ', engine='python')
    df_unmatch = df.query(' 原形 not in @synonym_dict.keys() ', engine='python')
    # 同義語に指定された単語を置き換え
    df_match = df_match.replace({'原形': synonym_dict})
    # 品詞を固有名詞に設定
    df_match['品詞'] = '固有名詞'
    # 結合
    df = pd.concat([df_match, df_unmatch]).sort_index()

    return df


def create_keywords(df, remove_words_list, target_hinshi):
    # 形態素解析DFから各列の要素をリストで取得
    midashi = list(df['表層形'])
    genkei = list(df['原形'])
    hinshi = list(df['品詞'])

    # sentences: [[midashi_1, genkei_1, hinshi_1], [midashi_2, ...], ...]
    sentences = [midashi]
    sentences.append(genkei)
    sentences.append(hinshi)
    sentences = np.array(sentences).T

    # 同一文の中で設定に合致したwordsをkeywordsに含める
    keywords = []
    words = set()
    for idx, sentence in enumerate(sentences):
        # 句点があれば
        if sentence[0] == '。':
            keywords.append(list(words))
            words = set()
            continue

        # 品詞がtarget_hinshiに含まれている and not (見出しが除去ワードリストに入っている or 原型が除去ワードリストに入っている)
        # and not (除去対象の品詞組み合わせである)
        if can_add_genkei2words(sentence, target_hinshi, remove_words_list):
            words.add((sentence[1], sentence[2]))
    return keywords


def create_sentence_combinations(keywords, remove_combi):
    # keywordsを基に単語ごとの組み合わせを計算
    sentence_combinations = [list(itertools.combinations(
        set(sentence), 2)) for sentence in keywords]
    sentence_combinations = [[tuple(sorted(words)) for words in sentence]
                             for sentence in sentence_combinations]

    # 品詞の辞書を取得
    hinshi_dict = get_hinshi_dict()
    # 感動詞の削除
    del hinshi_dict['kandoushi']
    for key in remove_combi.keys():
        if not remove_combi.get(key):
            del hinshi_dict[key]

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

    return sentence_combinations


def create_co_oc_df(keywords, sentence_combinations, all_data_size, category=''):
    combi_count = collections.Counter(sum(sentence_combinations, []))

    if not category:
        columns = ['単語a', '単語aの品詞', '単語b', '単語bの品詞',
                   'intersection_count']
        (on1_list, on2_list) = (['単語a', '単語aの品詞'],
                                ['単語b', '単語bの品詞'])
    else:
        columns = ['単語a', '単語aの品詞', '単語b', '単語bの品詞',
                   'category', 'intersection_count']
        (on1_list, on2_list) = (['単語a', '単語aの品詞', 'category'],
                                ['単語b', '単語bの品詞', 'category'])

    word_associates = []
    for key, value in combi_count.items():
        if not category:
            word_associates.append(
                [key[0][0], key[0][1], key[1][0], key[1][1], value])
        else:
            word_associates.append(
                [key[0][0], key[0][1], key[1][0], key[1][1], category, value])

    word_associates = pd.DataFrame(word_associates, columns=columns)

    word_count = collections.Counter(sum(keywords, []))
    if not category:
        word_count = [[key[0], key[1], value]
                      for key, value in word_count.items()]
        word_count = pd.DataFrame(word_count,
                                  columns=['word', 'word_type', 'count'])
    else:
        word_count = [[key[0], key[1], category, value]
                      for key, value in word_count.items()]
        word_count = pd.DataFrame(word_count,
                                  columns=['word', 'word_type', 'category', 'count'])

    word_associates = pd.merge(
        word_associates,
        word_count.rename(columns={'word': '単語a',
                                   'word_type': '単語aの品詞'}),
        on=on1_list,
        how='left'
    ).rename(
        columns={'count': 'count1'}
    ).merge(
        word_count.rename(columns={'word': '単語b',
                                   'word_type': '単語bの品詞'}),
        on=on2_list,
        how='left'
    ).rename(
        columns={'count': 'count2'}
    ).assign(
        union_count=lambda x: x.count1 + x.count2 - x.intersection_count
    ).reset_index(
        drop=True
    )

    # jaccard係数の作成
    word_associates['jaccard_coef'] = (word_associates['intersection_count'] /
                                       word_associates['union_count'])
    # dice係数の作成
    word_associates['dice_coef'] = (2*word_associates['intersection_count'] /
                                    (word_associates['count1'] + word_associates['count2']))
    # simpson係数作成
    simpson_coef = [intersection/min(count1, count2)
                    for intersection, count1, count2
                    in zip(word_associates['intersection_count'].tolist(),
                           word_associates['count1'].tolist(),
                           word_associates['count2'])]
    word_associates['simpson_coef'] = simpson_coef
    # 相互情報量作成
    pmi_coef = [math.log2((intersection*all_data_size)/(count1*count2))
                for intersection, count1, count2
                in zip(word_associates['intersection_count'],
                       word_associates['count1'],
                       word_associates['count2'])]
    word_associates['pmi_coef'] = pmi_coef

    return word_associates


# ネットワーク描画のメイン処理定義
def kyoki_word_network(target_num=250, file_name='3742_9_3_11_02', target_coef='共起頻度'):
    from pyvis.network import Network

    # got_net = Network(height="1000px", width="95%", bgcolor="#222222", font_color="white", notebook=True)
    got_net = Network(height="100%", width="100%",
                      bgcolor="#222222", font_color="white")
    # got_net = Network(height="1000px", width="95%", bgcolor="#FFFFFF", font_color="black", notebook=True)

    # set the physics layout of the network
    # got_net.barnes_hut()
    got_net.force_atlas_2based()
    got_data = pd.read_csv(f'tmp/{file_name}.csv')[:target_num]

    # カラム名変更
    got_data = got_data.rename(columns={target_coef: 'count'})

    sources = got_data['単語a']  # first
    targets = got_data['単語b']  # second
    weights = got_data['count']  # count

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
        node["title"] += "<br>共起:<br>" + \
            "<br>".join(neighbor_map[node["id"]])
        node["value"] = len(neighbor_map[node["id"]])

    return got_net


def create_network(file_name='kaijin_nijumenso', target_hinshi=['名詞'], target_num=250, remove_words='', remove_combi='',
                   target_words='', data_type='edogawa', is_used_3d=False, used_category=0, synonym='', selected_category=[],
                   target_coef='共起頻度', strength_max=10000, mrph_type='juman'):
    """
    共起ネットワークの作成

    Parameters
    ----------
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
    data_type: str, default='edogawa'
        入力データの種類（江戸川乱歩作品: 'edoagwa', csv: 'csv'）
    is_used_3d: bool, default=False
        3Dの共起ネットワークを表示するか否か
    used_category: int, default=0
        カテゴリーごとの描画を行う（1）か否（0）か
    synonym: str, default=''
        同義語設定
    selected_category: list, default=[]
        カテゴリーごとの描画において描画制限する
    target_coef: str, default='共起頻度'
        共起強度に何を用いるか
    strength_max: float, default=10000
        表示する共起強度の最大値
    mrph_type: str, default='juman'
        入力データが江戸川乱歩作品の場合に使用する形態素解析器

    Returns
    -------
    file_random_name: str
        入力と設定で絞り込んだcsvデータのファイル名
    co_oc_df: DataFrame
        入力と設定で絞り込んだcsvデータのDataFrame形式
    """
    # カテゴリーごとに表示する際の並び順を取得
    if data_type == 'edogawa':
        # カテゴリーごとの分析をしない もしくは 2D表示ならば
        if used_category == 0 or not is_used_3d:
            if mrph_type == 'juman':
                # jumanppにより形態素解析したDF取得
                df = get_jumanpp_df(file_name)
            else:
                # MeCabにより形態素解析されたDF取得
                df = get_mecab_with_category_df(file_name)
        # カテゴリーごとの分析をする かつ 3D表示ならば
        else:
            if mrph_type == 'juman':
                # jumanppにより形態素解析したDF取得
                df = get_jumanpp_df(file_name).rename(
                    columns={'章ラベル': 'カテゴリー'})
            else:
                # MeCabにより形態素解析されたDF取得
                df = get_mecab_with_category_df(file_name)
            if selected_category:
                df = df.query(' カテゴリー in @selected_category ')
    else:
        df = pd.read_csv(f'tmp/{file_name}.csv')
    # カラム名を統一
    df = df.rename(columns={'見出し': '表層形',
                            '原型': '原形',
                            '章ラベル': 'カテゴリー'})
    # 除去ワードリスト
    remove_words_list = remove_words.split('\r\n')

    # 同義語設定
    if synonym:
        df = modify_df_with_synonym(df, synonym)
        target_hinshi.append('固有名詞')

    # keywords, sentence_combinations, co_oc_dfの作成
    keywords_dict = {}
    sentence_combinations_dict = {}
    co_oc_df = pd.DataFrame()
    if used_category == 1 and is_used_3d:
        for cat in df['カテゴリー'].unique():
            keywords_dict[cat] = create_keywords(df.query(' カテゴリー==@cat '),
                                                 remove_words_list,
                                                 target_hinshi)
            sentence_combinations_dict[cat] = create_sentence_combinations(keywords_dict[cat],
                                                                           remove_combi)
            all_data_size = len(sum(keywords_dict[cat], []))
            tmp_df = create_co_oc_df(keywords_dict[cat],
                                     sentence_combinations_dict[cat],
                                     all_data_size,
                                     category=cat)
            co_oc_df = pd.concat([co_oc_df, tmp_df]).reset_index(drop=True)
    else:
        key_name = 'all'
        keywords_dict[key_name] = create_keywords(df,
                                                  remove_words_list,
                                                  target_hinshi)
        sentence_combinations_dict[key_name] = create_sentence_combinations(keywords_dict[key_name],
                                                                            remove_combi)
        all_data_size = len(sum(keywords_dict[key_name], []))
        co_oc_df = create_co_oc_df(keywords_dict[key_name],
                                   sentence_combinations_dict[key_name],
                                   all_data_size)
    # カラム名の変更
    co_oc_df = co_oc_df.rename(columns={'category': 'カテゴリー',
                                        'count1': '単語aの出現頻度',
                                        'count2': '単語bの出現頻度',
                                        'union_count': '単語aと単語bの和集合',
                                        'intersection_count': '共起頻度',
                                        'jaccard_coef': 'Jaccard係数',
                                        'dice_coef': 'Dice係数',
                                        'simpson_coef': 'Simpson係数',
                                        'pmi_coef': '相互情報量'})
    # 指定ワードが含まれるレコードのみ抽出
    if target_words:
        new_co_oc_df = pd.DataFrame()
        for tw in target_words.split('\r\n'):
            new_co_oc_df = pd.concat([new_co_oc_df,
                                      co_oc_df.query(' @tw in 単語a or @tw in 単語b ')])
        co_oc_df = new_co_oc_df.sort_values(
            target_coef,
            ascending=False
        ).drop_duplicates(
            subset=['単語a', '単語b']
        ).reset_index(drop=True)
    # 表示する共起強度を制限
    co_oc_df = co_oc_df[co_oc_df[target_coef]
                        <= strength_max].reset_index(drop=True)
    # target_coefでソート
    co_oc_df = co_oc_df.sort_values(
        target_coef, ascending=False).reset_index(drop=True)
    # 所定の構造でCSVファイルに出力
    file_random_name = create_random_string(32)
    co_oc_df.to_csv(f'tmp/{file_random_name}.csv',
                    index=False, encoding='utf_8_sig')
    # 小数点以下2桁で丸める
    co_oc_df = co_oc_df.round(2)

    try:
        # 2Dの共起ネットワークHTML作成
        if not is_used_3d:
            got_net = kyoki_word_network(target_num=target_num,
                                         file_name=file_random_name,
                                         target_coef=target_coef)
            got_net.write_html(f'tmp/{file_random_name}.html')
        return file_random_name, co_oc_df
    except:
        return '', '', ''
