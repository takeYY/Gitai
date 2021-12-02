import MeCab
import timeout_decorator
from pyknp import Juman
from src.get_data import mecab_divide_dict, juman_divide_dict


def get_morphological_analysis_dict():
    return dict(MeCab='MeCab', NEologd='NEologd', Jumanpp='Jumanpp',
                output_sample_mecab='MeCab（NEologd）の出力例', output_sample_jumanpp='Jumanppの出力例')


def get_morphological_analysis_description_dict():
    description = ["""高速に解析ができ、日本語テキストの中では最もよく使われています。
                        とりあえず解析したい場合は、MeCabを選択すると良いでしょう。""",
                   """MeCabの解析時に使用する辞書のことで、辞書の更新を頻繁に行っています。
                        そのため、新語・固有名詞の解析が得意で語彙数も多いです。""",
                   """MeCabよりも高精度で単語の分割、品詞の判別が可能です。
                        ただし、欠点として解析に時間がかかり、単語の分割が細かいことが挙げられます。""",
                   """インスタ映え ==>
                        　表層形, 品詞, 品詞細分類(1)
                        　インスタ映え, 名詞, 固有名詞

                        バナナオレが飲みたい ==>
                        　表層形, 品詞, 品詞細分類(1)
                        　バナナオレ, 名詞, 一般
                        　が, 助詞, 格助詞
                        　飲み, 動詞, 自立
                        　たい, 助動詞, *
                        """,
                   """インスタ映え ==>
                        　見出し, 品詞, 品詞細分類
                        　インスタ, 名詞, 普通名詞
                        　映え, 名詞, 普通名詞

                        バナナオレが飲みたい ==>
                        　見出し, 品詞, 品詞細分類
                        　バナナ, 名詞, 普通名詞
                        　オレ, 名詞, 普通名詞
                        　が, 助詞, 格助詞
                        　飲む, 動詞, *
                        　たい, 接尾辞, 形容詞性述語接尾辞"""]
    return {value: description[idx] for idx, value in enumerate(get_morphological_analysis_dict().values())}


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
