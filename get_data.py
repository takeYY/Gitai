import pandas as pd


def get_hinshi_dict():
    return dict(all='全て(名詞・動詞・形容詞・副詞)', meishi='名詞', doushi='動詞', keiyoushi='形容詞', fukushi='副詞')


def get_edogawa_df():
    return pd.read_csv('csv/edogawa_list.csv')


def get_khcoder_df(file_name):
    return pd.read_csv(f'csv/khcoder/{file_name}.csv')


def get_basic_data(title='ホーム', active_url='home'):
    return dict(title=title, active_url=active_url)


def get_novels_tuple(novels=get_edogawa_df(), col1='name', col2='file_name'):
    novels_col1 = list(novels[col1])
    novels_col2 = list(novels[col2])
    return list(zip(novels_col1, novels_col2))
