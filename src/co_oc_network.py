from flask import flash
import math
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import itertools
import collections
import networkx as nx
import plotly.graph_objects as go
from werkzeug.utils import secure_filename
from src.get_data import get_jumanpp_df, get_mecab_df, get_datetime_now, get_hinshi_dict, create_random_string, create_category_df
from src.co_oc_3d_network import create_word_frequency, append_edge_dictionary, append_node_dictionary
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


# 選択された品詞である or ストップワード（強制除去語）リストにない単語であるか判定
def can_add_genkei2words(sentence, target_hinshi, remove_words_list, target_words: list):
    midashi = sentence[0]
    genkei = sentence[1]
    hinshi = sentence[2]

    # 強制抽出語であればどんな条件に関係なく追加
    if target_words and midashi in target_words or genkei in target_words:
        return True
    # 品詞が可視化対象の品詞に含まれていない場合
    if not hinshi in target_hinshi:
        return False
    # 見出し や 原形がストップワード（強制除去語）リストに含まれている場合
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
    try:
        file.save(os.path.join(UPLOAD_FOLDER, csv_filename))
    except:
        file.save(os.path.join('/code/tmp', csv_filename))

    return input_filename, csv_filename, dict()


def modify_df_with_synonym(tmp_df: pd.DataFrame, synonym: str) -> pd.DataFrame:
    # key:置換対象の文字列, value:置換後の文字列
    # ex) synonyms: [{'黄金': '黄金仮面', '仮面': '黄金仮面'}]
    synonyms = []
    synonym_items = [s for s in synonym.split('・') if s != '']
    for item in synonym_items:
        synonym_dict = {}
        item_split = [s for s in item.split('\r\n') if s != '']
        replace_word = item_split[0]
        target_word = item_split[1]
        for tw in target_word.split(','):
            synonym_dict[tw] = replace_word
        synonyms.append(synonym_dict)

    for syno_dict in synonyms:
        df_match = tmp_df.query(' 原形 in @syno_dict.keys() or 表層形 in @syno_dict.keys() ',
                                engine='python')
        target = df_match.index.tolist()
        target_tmp = target.copy()
        i = 0
        while True:
            tgt = target_tmp[i]
            for key in syno_dict.keys():
                t_df = tmp_df[tgt-2:tgt+2].query(' 原形==@key or 表層形==@key ',
                                                 engine='python')
                if t_df.empty:
                    try:
                        target.remove(tgt)
                    except:
                        print('target:', target)
                        print('tgt:', tgt)
            i += 1
            if i == len(target_tmp):
                break
        for tgt in target:
            new_df = tmp_df[tgt-2:tgt+2].replace({'原形': syno_dict})
            new_df.at[tgt, '品詞'] = '固有名詞'
            tmp_df.iloc[tgt-2:tgt+2] = new_df

    return tmp_df


def create_keywords(df, remove_words_list, target_words, target_hinshi):
    """
    共起に使用する(単語, 品詞)を文ごとにリスト化する

    Parameters
    ----------
    df: pd.DataFrame
        共起ネットワークを構築する対象のデータ
    remove_words_list: list of str
        ストップワードのリスト
    target_words: list of str
        強制抽出語のリスト
    target_hinshi: list of str
        可視化対象の品詞のリスト

    Returns
    -------
    keywords: list of tuple
        ex) [
                [('少年', '名詞'), ('探偵', '名詞')],
                [('先生', '名詞'), ('明智', '名詞')],
                [('受話器', '名詞'), ('小林', '名詞'), ('横', '名詞'), ('先生', '名詞'), ('明智', '名詞')]
            ]
    """
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

        # 見出しか原型が強制抽出語に含まれている or 品詞がtarget_hinshiに含まれている
        # and not (見出しがストップワード（強制除去語）リストに入っている or 原型がストップワード（強制除去語）リストに入っている)
        # and not (除去対象の品詞組み合わせである)
        if can_add_genkei2words(sentence, target_hinshi, remove_words_list, target_words):
            words.add((sentence[1], sentence[2]))

    return keywords


def create_sentence_combinations(keywords, remove_combi):
    """
    単語の組み合わせを作成

    Parameters
    ----------
    keywords: list of tuple
        共起に使用する(単語, 品詞)を文ごとにリスト化したもの
    remove_combi: dict
        削除する品詞の組み合わせ辞書

    Returns
    -------
    sentence_combinations: list of tuple
        共起の組み合わせ
        ex) [
                [(('少年', '名詞'), ('探偵', '名詞'))],
                [(('先生', '名詞'), ('明智', '名詞'))],
                [
                    (('横', '名詞'), ('先生', '名詞')),
                    (('横', '名詞'), ('小林', '名詞')),
                    (('受話器', '名詞'), ('よこ', '名詞')),
                    (('横', '名詞'), ('明智', '名詞')),
                    (('先生', '名詞'), ('小林', '名詞')),
                    (('受話器', '名詞'), ('先生', '名詞')),
                    (('先生', '名詞'), ('明智', '名詞')),
                    (('受話器', '名詞'), ('小林', '名詞')),
                    (('小林', '名詞'), ('明智', '名詞')),
                    (('受話器', '名詞'), ('明智', '名詞'))
                ]
            ]
    """
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
    # 型変更
    got_data = got_data.astype({'単語a': str, '単語b': str})

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


def create_2D_network_figure(df, target_num, fig, target_coef):
    # 新規グラフを作成
    G = nx.Graph()

    # カラム名変更
    df = df.rename(columns={target_coef: 'count'})

    # タプル作成
    kyouki_tuple = [(f'{first}__{first_type}', f'{second}__{second_type}', count)
                    for first, second, count, first_type, second_type
                    in zip(df['単語a'],
                           df['単語b'],
                           df['count'],
                           df['単語aの品詞'],
                           df['単語bの品詞'])]

    # ノードとエッジを追加
    list_edge = kyouki_tuple[:target_num]
    G.add_weighted_edges_from(list_edge)

    # nodeの連結nodeを取得
    neighbors_list = ['<br>'.join(list(nx.all_neighbors(G, t)))
                      for t in list(G.nodes())]

    # 各単語の頻度を計算
    word_frequency = create_word_frequency(df['単語a'].tolist(),
                                           df['単語aの品詞'].tolist(),
                                           df['単語aの出現頻度'].tolist())
    word_frequency = create_word_frequency(df['単語b'].tolist(),
                                           df['単語bの品詞'].tolist(),
                                           df['単語bの出現頻度'].tolist(),
                                           word_frequency=word_frequency)

    # 各ノード情報を記載
    for idx, text in enumerate(list(G.nodes())):
        word, word_type = text.split('__')
        G.nodes[text]['node_info'] = {
            '単語ID': idx+1,
            '単語': word,
            '品詞': word_type,
            '出現頻度': word_frequency[text],
            '共起': f'<br>{neighbors_list[idx]}',
        }

    # 図のレイアウトを決める。kの値が小さい程図が密集
    pos = nx.spring_layout(G, k=0.7, weight=None)

    # ノードの位置を設定
    for node in G.nodes():
        G.nodes[node]["pos"] = pos[node]

    # エッジの設定
    if target_coef == '共起頻度':
        edge_group = [10, 50, 100]
    elif target_coef == '相互情報量':
        edge_group = [5, 7.5, 10]
    else:
        edge_group = [0.1, 0.25, 0.5]
    edges = dict(e0=dict(x=[], y=[], weight=[]),
                 e1=dict(x=[], y=[], weight=[]),
                 e2=dict(x=[], y=[], weight=[]),
                 e3=dict(x=[], y=[], weight=[]),
                 e4=dict(x=[], y=[], weight=[]),)
    for e in G.edges():
        x0, y0 = G.nodes[e[0]]['pos']
        x1, y1 = G.nodes[e[1]]['pos']
        weight = G.edges[e]['weight']
        x_list = [x0, x1, None]
        y_list = [y0, y1, None]
        if weight < edge_group[0]:
            edges = append_edge_dictionary(edges, 1,
                                           x=x_list, y=y_list, z=None,
                                           weight=weight)
        elif edge_group[0] <= weight < edge_group[1]:
            edges = append_edge_dictionary(edges, 2,
                                           x=x_list, y=y_list, z=None,
                                           weight=weight)
        elif edge_group[1] <= weight < edge_group[2]:
            edges = append_edge_dictionary(edges, 3,
                                           x=x_list, y=y_list, z=None,
                                           weight=weight)
        else:
            edges = append_edge_dictionary(edges, 4,
                                           x=x_list, y=y_list, z=None,
                                           weight=weight)

    line_width = [1.0, 2.0, 3.0, 4.0]
    for idx in range(len(line_width)):
        if idx == 3:
            name_text = f'{edge_group[2]} <='
        else:
            name_text = f'< {edge_group[idx]}'
        fig.add_trace(go.Scatter(
            name=name_text,
            x=edges[f'e{idx+1}']['x'],
            y=edges[f'e{idx+1}']['y'],
            mode='lines',
            opacity=0.5,
            legendgroup='edges',
            legendgrouptitle=dict(text='count'),
            line=dict(width=line_width[idx]),
            customdata=edges[f'e{idx+1}']['weight'],
            hovertemplate="count: %{customdata}<extra></extra>"
        ))

    # ノードの設定
    node_group = [50, 100, 200, 300]
    nodes = dict(n0=dict(x=[], y=[], z=[], frequency=[], text=[], info=[]),
                 n1=dict(x=[], y=[], z=[], frequency=[], text=[], info=[]),
                 n2=dict(x=[], y=[], z=[], frequency=[], text=[], info=[]),
                 n3=dict(x=[], y=[], z=[], frequency=[], text=[], info=[]),
                 n4=dict(x=[], y=[], z=[], frequency=[], text=[], info=[]),)
    for n in G.nodes():
        x, y = G.nodes[n]['pos']
        frequency = word_frequency.get(n)
        text = n.split('__')[0]
        info = '<br>'.join(
            [f'{k}: {value}' for k, value in G.nodes[n]['node_info'].items()])
        if frequency < node_group[0]:
            nodes = append_node_dictionary(nodes, 1,
                                           x, y, None,
                                           frequency, text, info)
        elif node_group[0] <= frequency < node_group[1]:
            nodes = append_node_dictionary(nodes, 2,
                                           x, y, None,
                                           frequency, text, info)
        elif node_group[1] <= frequency < node_group[2]:
            nodes = append_node_dictionary(nodes, 3,
                                           x, y, None,
                                           frequency, text, info)
        else:
            nodes = append_node_dictionary(nodes, 4,
                                           x, y, None,
                                           frequency, text, info)

    marker_size = [10, 20, 30, 40]
    for idx in range(len(marker_size)):
        if idx == 3:
            name_text = f'{node_group[2]} <='
        else:
            name_text = f'< {node_group[idx]}'
        fig.add_trace(go.Scatter(
            name=name_text,
            x=nodes[f'n{idx+1}']['x'],
            y=nodes[f'n{idx+1}']['y'],
            text=nodes[f'n{idx+1}']['text'],
            customdata=nodes[f'n{idx+1}']['info'],
            textposition='middle center',
            mode='markers+text',
            legendgroup='nodes',
            legendgrouptitle=dict(text='frequency'),
            marker=dict(size=marker_size[idx],
                        line=dict(width=2),
                        opacity=0.5,
                        colorscale='jet'),
            textfont=dict(size=10),
            hovertemplate="%{customdata}<extra></extra>",
        ))

    return fig


def create_2D_detail_network(df, target_num=50, target_coef='共起頻度', html_random_name=''):
    fig = go.Figure()
    fig = create_2D_network_figure(df, target_num, fig, target_coef)

    layout = go.Layout(
        showlegend=True,
        legend=dict(
            borderwidth=2,
        ),
        scene=dict(
            xaxis=dict(backgroundcolor='rgb(150, 100, 100)'),
            yaxis=dict(backgroundcolor='rgb(100, 150, 100)'),
        ),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        clickmode='select+event',
    )

    fig.update_layout(layout)

    fig.write_html(f'tmp/{html_random_name}.html', auto_open=False)

    return html_random_name


def create_network(file_name='kaijin_nijumenso', target_hinshi=['名詞'], target_num=250, remove_words=[], remove_combi='',
                   target_words=[], data_type='edogawa', is_used_3d=False, used_category=0, synonym='', selected_category=[],
                   target_coef='共起頻度', strength_max=10000, mrph_type='juman', co_oc_freq_min=2, dimension=2):
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
    remove_words: list of str, default=[]
        共起に含めたくないストップワード（強制除去語）のリスト
    remove_combi: dict, default=''
        除去対象の品詞組み合わせ
    target_words: list of str, default=[]
        指定した単語の共起のみ表示するリスト
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
    co_oc_freq_min: int, default=2
        共起頻度の最小値
    dimension: int, default=2
        表示形式

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
                df = get_mecab_df(file_name)
        # カテゴリーごとの分析をする かつ 3D表示ならば
        else:
            if mrph_type == 'juman':
                # jumanppにより形態素解析したDF取得
                df = get_jumanpp_df(file_name).rename(
                    columns={'章ラベル': 'カテゴリー'})
            else:
                # MeCabにより形態素解析されたDF取得
                df = get_mecab_df(file_name)
            if selected_category:
                # 見出しからカテゴリー作成後選択したカテゴリーに絞る
                df = create_category_df(df).query(
                    ' カテゴリー in @selected_category ')
    else:
        df = pd.read_csv(f'tmp/{file_name}.csv')
    # カラム名を統一
    df = df.rename(columns={'見出し': '表層形',
                            '原型': '原形'})

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
                                                 remove_words,
                                                 target_words,
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
                                                  remove_words,
                                                  target_words,
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
    # 共起頻度の最小値以上に制限
    co_oc_df = co_oc_df.query(
        ' @co_oc_freq_min <= 共起頻度 ').reset_index(drop=True)
    # 強制抽出語が含まれるレコードのみ抽出
    if target_words:
        new_co_oc_df = pd.DataFrame()
        for tw in target_words:
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
        # 2D共起ネットワークHTML作成（詳細バージョン）
        if dimension == 4:
            create_2D_detail_network(
                co_oc_df, target_num, target_coef, file_random_name)
        # 2Dの共起ネットワークHTML作成（シンプルバージョン）
        elif not is_used_3d:
            got_net = kyoki_word_network(target_num=target_num,
                                         file_name=file_random_name,
                                         target_coef=target_coef)
            got_net.write_html(f'tmp/{file_random_name}.html')
        return file_random_name, co_oc_df
    except:
        import traceback
        traceback.print_exc()
        return '', ''
