import pandas as pd
import datetime
import timeout_decorator
from pyknp import Juman


def get_hinshi_dict():
    return dict(meishi='名詞', doushi='動詞', keiyoushi='形容詞', fukushi='副詞', kandoushi='感動詞')


def get_edogawa_df():
    return pd.read_csv('csv/edogawa.csv')


def get_edogawa_detail_df():
    return pd.read_csv('csv/edogawa_detail.csv')


def get_original_text_df():
    return pd.read_csv('csv/original_text.csv')


def get_edogawa_merge_df():
    edogawa = get_edogawa_df()
    edogawa_detail = get_edogawa_detail_df()
    original_text = get_original_text_df()
    edogawa_merge = pd.merge(edogawa, edogawa_detail, on='reader_id')
    edogawa_merge = pd.merge(edogawa_merge, original_text, on='reader_id')
    return edogawa_merge


def get_edogawa_merge_with_rows_df():
    edogawa_merge = get_edogawa_merge_df()
    rows_list = []
    edogawa = get_edogawa_df()
    for idx, rows in edogawa.iterrows():
        row_name = rows['name']
        df = edogawa_merge.query(' name == @row_name ')
        rows_list.append(len(df))
    edogawa_detail = get_edogawa_detail_df()
    original_text = get_original_text_df()
    edogawa['rows_num'] = rows_list
    edogawa_merge = pd.merge(edogawa, edogawa_detail, on='reader_id')
    edogawa_merge = pd.merge(edogawa_merge, original_text, on='reader_id')
    return edogawa_merge


def get_khcoder_df(file_name):
    return pd.read_csv(f'csv/khcoder/{file_name}.csv')


def get_jumanpp_df(file_name):
    return pd.read_csv(f'csv/jumanpp/{file_name}.csv')


def get_basic_data(title='ホーム', active_url='home'):
    return dict(title=title, active_url=active_url)


def get_novels_tuple(novels=get_edogawa_df(), col1='name', col2='file_name'):
    novels_col1 = list(novels[col1])
    novels_col2 = list(novels[col2])
    return list(zip(novels_col1, novels_col2))


def mecab_divide_dict():
    return {'surface': '表層形', 'hinshi': '品詞', 'hinshi_detail_1': '品詞細分類(1)', 'hinshi_detail_2': '品詞細分類(2)',
            'hinshi_detail_3': '品詞細分類(3)', 'katsuyou_type': '活用型', 'katsuyou_form': '活用形', 'genkei': '原形',
            'yomi': '読み', 'hatsuon': '発音'}


def juman_divide_dict():
    return {'midashi': '見出し', 'yomi': '読み', 'genkei': '原形', 'hinshi': '品詞', 'bunrui': '品詞細分類',
            'katsuyou1': '活用型', 'katsuyou2': '活用形', 'imis': '意味情報', 'repname': '代表表記'}


def get_datetime_now():
    return datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S')


def dict_in_list2csv(dict_in_list, divide_dict):
    # 分類される要素をキーとし、空のリストを初期値に設定
    df_cols = {}
    for div_key in divide_dict.keys():
        df_cols[div_key] = []
    # 辞書の各valueに分類結果追加
    for dic in dict_in_list:
        for div_key in divide_dict.keys():
            df_cols[div_key].append(dic.get(div_key, '*'))
    # DataFrame作成
    df = pd.DataFrame(df_cols).rename(columns=divide_dict)
    # DataFrameをcsvとしてtmpに保存
    now = get_datetime_now()
    df.to_csv(f'tmp/{now}.csv', index=False, encoding='utf_8_sig')
    return df, now


@timeout_decorator.timeout(5, use_signals=False)
def get_juman_mrph(text):
    juman = Juman()
    result = juman.analysis(text)
    mrph_list = []
    for mrph in result.mrph_list():
        juman_dict = {}
        juman_dict['midashi'] = mrph.midasi
        juman_dict['yomi'] = mrph.yomi
        juman_dict['genkei'] = mrph.genkei
        juman_dict['hinshi'] = mrph.hinsi
        juman_dict['bunrui'] = mrph.bunrui
        juman_dict['katsuyou1'] = mrph.katuyou1
        juman_dict['katsuyou2'] = mrph.katuyou2
        juman_dict['imis'] = mrph.imis
        juman_dict['repname'] = mrph.repname
        mrph_list.append(juman_dict)
    return mrph_list
