import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly
from get_data import create_random_string, get_plotly_symbols, get_plotly_text_positions


def get_df_from_csv_filename(mrph_type, csv_filename):
    if mrph_type == 'mecab':
        return pd.read_csv(f'csv/mecab_with_category/{csv_filename}.csv')
    if mrph_type == 'juman':
        return pd.read_csv(f'csv/jumanpp/{csv_filename}.csv').rename(columns={'原型': '原形'})

    return pd.read_csv(f'tmp/{csv_filename}.csv')


def get_csv_mrph_type(df):
    columns = df.columns.tolist()
    if {'表層形', '品詞'}.issubset(columns):
        return 'mecab'
    elif {'見出し', '品詞'}.issubset(columns):
        return 'juman'
    else:
        return ''


def get_mrph_column(mrph_type):
    if mrph_type == 'mecab':
        return ['表層形', '品詞', '原形']
    elif mrph_type == 'juman':
        return ['見出し', '品詞', '原形']
    else:
        return []


def valid_agg_columns(csv_filename):
    mecab_columns = set(get_mrph_column('mecab'))
    juman_columns = set(get_mrph_column('juman'))

    df = pd.read_csv(f'tmp/{csv_filename}.csv')
    return mecab_columns.issubset(df.columns) or juman_columns.issubset(df.columns)


def get_unique_hinshi_dict(mrph_type, csv_filename):
    df = get_df_from_csv_filename(mrph_type, csv_filename)
    if not mrph_type:
        mrph_type = get_csv_mrph_type(df)
        if not mrph_type:
            return dict()

    mrph_columns = get_mrph_column(mrph_type)
    limited_columns = mrph_columns[:2]
    basic_type = mrph_columns[0]

    return df[limited_columns].groupby('品詞')\
                              .agg('count')\
                              .to_dict()\
                              .get(basic_type)


def create_figure(fig, agg_df):
    # 使用可能なsymbol
    all_symbols = get_plotly_symbols()
    # テキストポジションのリスト
    text_positions = get_plotly_text_positions()
    # figureの構築
    fig = go.Figure()
    for idx, hinshi in enumerate(agg_df['品詞'].unique().tolist()):
        tmp_df = agg_df.query(' 品詞==@hinshi ')
        symbol = all_symbols[idx]
        fig.add_trace(go.Scatter(
            name=hinshi,
            x=tmp_df['ランキング'],
            y=tmp_df['出現頻度'],
            text=tmp_df['単語'],
            textposition=[text_positions[i % len(text_positions)]
                          for i in range(len(tmp_df))],
            customdata=[
                f'単語：{rows["単語"]}<br><br>ランキング：{rows["ランキング"]}<br>品詞：{rows["品詞"]}<br>出現頻度：{rows["出現頻度"]}'
                for idx, rows in tmp_df.iterrows()],
            mode='markers+text',
            marker_symbol=[symbol]*len(tmp_df),
            hovertemplate="%{customdata}<extra></extra>",
        ))

    return fig


def create_aggregation(mrph_type, csv_name, target_hinshi=['名詞']):
    df = get_df_from_csv_filename(mrph_type, csv_name)
    mrph_columns = get_mrph_column(mrph_type) if mrph_type\
        else get_mrph_column(get_csv_mrph_type(df))
    # 表層形 or 見出し
    basic_type = mrph_columns[0]
    # 原形 or 原型
    origin_type = mrph_columns[2]

    df = df.query(' 品詞 in @target_hinshi ').reset_index(drop=True)
    # 集計データ
    agg_df = df[mrph_columns].groupby([basic_type, '品詞'])\
                             .agg('count')\
                             .query(' 品詞 in @target_hinshi ')\
                             .rename(columns={origin_type: '出現頻度'})\
                             .sort_values('出現頻度', ascending=False)\
                             .reset_index().reset_index()\
                             .rename(columns={'index': 'ランキング', basic_type: '単語'})
    # ランキングは1を最初にする
    agg_df['ランキング'] = agg_df['ランキング'] + 1
    # figureの取得
    fig = create_figure(go.Figure(), agg_df)

    layout = go.Layout(
        showlegend=True,
        legend=dict(
            borderwidth=2,
        ),
        plot_bgcolor='rgba(0, 0, 0, 0)',
        paper_bgcolor='rgba(0, 0, 0, 0)',
        clickmode='select',
    )
    fig.update_layout(layout)

    html_random_name = create_random_string(32)
    # 集計データの出力
    agg_df.to_csv(f'tmp/{html_random_name}.csv', index=False)
    # 集計グラフのhtml出力
    fig.write_html(f'tmp/{html_random_name}.html', auto_open=False)

    return agg_df, html_random_name
