import pandas as pd
import itertools
import collections
import datetime
from get_data import get_jumanpp_df


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


def create_network(file_name='kaijin_nijumenso', target_hinshi=['名詞'], target_num=250, remove_words=''):
    df = get_jumanpp_df(file_name)
    remove_words_list = remove_words.split('\r\n')

    midashi = list(df['見出し'])
    genkei = list(df['原型'])
    hinshi = list(df['品詞'])
    sentences = []
    for i in range(len(midashi)):
        sentences.append([midashi[i], genkei[i], hinshi[i]])

    keywords = []
    words = []
    for sentence in sentences:
        if sentence[0] != '。':
            if sentence[2] in target_hinshi and not (sentence[0] in remove_words_list or sentence[1] in remove_words_list):
                words.append(sentence[1])
        else:
            keywords.append(words)
            words = []

    sentence_combinations = [list(itertools.combinations(
        set(sentence), 2)) for sentence in keywords]
    sentence_combinations = [[tuple(sorted(words)) for words in sentence]
                             for sentence in sentence_combinations]
    target_combinations = []
    for sentence in sentence_combinations:
        target_combinations.extend(sentence)

    ct = collections.Counter(target_combinations)

    # 所定の構造でCSVファイルに出力
    now = datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
    pd.DataFrame([{'first': i[0][0], 'second': i[0][1], 'count': i[1]}
                  for i in ct.most_common()]).to_csv(f'tmp/{now}.csv', index=False)

    try:
        # 処理の実行
        got_net = kyoki_word_network(target_num=target_num, file_name=now)
        got_net.write_html(f'tmp/{now}.html')
        return now
    except:
        return ''
