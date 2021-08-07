import MeCab
import timeout_decorator
from pyknp import Juman
from get_data import mecab_divide_dict, juman_divide_dict


@timeout_decorator.timeout(29, use_signals=False)
def get_mecab_mrph(text):
    tagger = MeCab.Tagger(
        '-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd'
    )
    # MeCabの分類リスト取得
    divide_keys = list(mecab_divide_dict().keys())
    # MeCabによる形態素解析
    mecab_parse = tagger.parse(text)
    mecab_line = [line for line in mecab_parse.split('\n')]
    mrph_list = []
    # 分類をキー、結果をvalueとしたmecab_dictをmrph_listに追加
    for line in mecab_line:
        mecab_dict = {}
        line_split = line.split('\t')
        if line_split[0] == 'EOS':
            break

        if line_split[0] == '\r':
            continue

        mecab_dict['surface'] = line_split[0]
        values = line_split[1].split(',')
        for idx, value in enumerate(values):
            mecab_dict[divide_keys[idx+1]] = value
        mrph_list.append(mecab_dict)

    return mrph_list


@timeout_decorator.timeout(29, use_signals=False)
def get_juman_mrph(text):
    mrph_list = []
    for t in text.split('。'):
        if not t:
            continue
        juman = Juman()
        result = juman.analysis(t.replace('\n', '') + '。')
        result_list = []
        # 分類をキー、結果をvalueとしたjuman_dictをresult_listに追加
        for mrph in result.mrph_list():
            juman_dict = {}
            if mrph.midasi == '\r':
                continue
            juman_dict['midashi'] = mrph.midasi
            juman_dict['yomi'] = mrph.yomi
            juman_dict['genkei'] = mrph.genkei
            juman_dict['hinshi'] = mrph.hinsi
            juman_dict['bunrui'] = mrph.bunrui
            juman_dict['katsuyou1'] = mrph.katuyou1
            juman_dict['katsuyou2'] = mrph.katuyou2
            juman_dict['imis'] = mrph.imis
            juman_dict['repname'] = mrph.repname
            result_list.append(juman_dict)
        mrph_list.extend(result_list)

    return mrph_list


def mrph_analysis(mrph_type, text):
    # MeCabによる解析
    if mrph_type == 'mecab':
        try:
            # MeCabによる形態素解析
            mrph_result = get_mecab_mrph(text)
        except:
            # 解析に29秒以上かかった場合
            mrph_result = ''
        # MeCabの分類辞書
        divide_dict = mecab_divide_dict()

    # Jumanによる解析
    elif mrph_type == 'juman':
        try:
            # Jumanppによる形態素解析
            mrph_result = get_juman_mrph(text)
        except:
            # 29秒以上かかった場合
            mrph_result = ''
        # Jumanppの分類辞書
        divide_dict = juman_divide_dict()
    else:
        mrph_result, divide_dict = '', ''

    return mrph_result, divide_dict
