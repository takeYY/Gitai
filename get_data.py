import pandas as pd


def get_hinshi_dict():
    return dict(meishi='名詞', doushi='動詞', keiyoushi='形容詞', keiyoudoushi='形容動詞',
                fukushi='副詞', kandoushi='感動詞')


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
