import MeCab
import timeout_decorator
from pyknp import Juman
import pandas as pd
from src.get_data import mecab_divide_dict


def get_morphological_analysis_dict():
    return dict(MeCab='MeCab', NEologd='NEologd', Jumanpp='Jumanpp',
                output_sample_mecab='MeCab（NEologd）の出力例', output_sample_jumanpp='Jumanppの出力例')


@timeout_decorator.timeout(29, use_signals=False)
def get_mecab_mrph(text):
    tagger = MeCab.Tagger(
        '-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd'
    )
    # MeCabの分類リスト取得
    divide_values = list(mecab_divide_dict().values())
    # MeCabによる形態素解析
    mecab_parse = tagger.parse(text)
    mecab_line = [line for line in mecab_parse.split('\n')]
    mrph_list = []
    # 分類をキー、結果をvalueとしたmecab_dictをmrph_listに追加
    for line in mecab_line:
        mecab_dict = {}
        line_split = line.split('\t')
        surface = line_split[0]
        if surface == 'EOS':
            break
        if surface == '\r':
            continue

        mecab_dict['表層形'] = surface
        values = line_split[1].split(',')
        for idx, value in enumerate(values):
            mecab_dict[divide_values[idx+1]] = value
        mrph_list.append(mecab_dict)
    return pd.DataFrame(mrph_list)


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
            juman_dict['見出し'] = mrph.midasi
            juman_dict['読み'] = mrph.yomi
            juman_dict['原形'] = mrph.genkei
            juman_dict['品詞'] = mrph.hinsi
            juman_dict['品詞細分類'] = mrph.bunrui
            juman_dict['活用型'] = mrph.katuyou1
            juman_dict['活用形'] = mrph.katuyou2
            juman_dict['意味情報'] = mrph.imis
            juman_dict['代表表記'] = mrph.repname
            result_list.append(juman_dict)
        mrph_list.extend(result_list)

    return pd.DataFrame(mrph_list)


def mrph_analysis(mrph_type, text) -> pd.DataFrame:
    """
    形態素解析の処理

    Parameters
    ----------
    mrph_type: str
        形態素解析器の種類, ['mecab', 'juman']
    text: str
        形態素解析対象のテキスト

    Returns
    -------
    mrph_df: pd.DataFrame
        形態素解析済みのDataFrame
    """
    # MeCabによる解析
    if mrph_type == 'mecab':
        try:
            # MeCabによる形態素解析
            mrph_df = get_mecab_mrph(text)
        except:
            # 解析に29秒以上かかった場合
            mrph_df = pd.DataFrame()

    # Jumanによる解析
    elif mrph_type == 'juman':
        try:
            # Jumanppによる形態素解析
            mrph_df = get_juman_mrph(text)
        except:
            # 29秒以上かかった場合
            mrph_df = pd.DataFrame()
    else:
        mrph_df = pd.DataFrame()

    return mrph_df
