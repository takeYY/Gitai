import pandas as pd
from mathematical_formula import get_count_formula, get_jaccard_formula, get_dice_formula, get_simpson_formula, get_pmi_formula, get_co_oc_formula_description


def detail_description(title: str = None, description: str = None, formula: str = None) -> str:
    html_text = ''
    if title:
        html_text += fr"""<h5>{title}</h5>"""
    if description:
        html_text += fr"""<p>{description}</p>"""
    if formula:
        html_text += fr"""<div class='text-center'>{formula}</div>"""

    return html_text


def detail_table_description(title: str = None, description: str = None, table: pd.DataFrame = None) -> str:
    html_text = ''
    if title:
        html_text += fr"""<h5>{title}</h5>"""
    if description:
        html_text += fr"""<p>{description}</p>"""
    if table is not None:
        html_text += fr"""<table class='table table-hover table-striped table-sm'>
                            <thead class='thead-dark'>
                              <tr>"""
        for column in table.columns:
            html_text += fr"""<th scope='col'>{column}</th>"""
        html_text += fr"""</tr></thead><tbody>"""
        for idx, rows in table.iterrows():
            html_text += fr"""<tr>"""
            for column in table.columns:
                html_text += fr"""<th>{rows[column]}</th>"""
            html_text += fr"""</tr>"""
        html_text += fr"""</tbody></table>"""

    return html_text


def co_oc_strength_description():
    return dict(frequency=detail_description('共起頻度',
                                             frequency_description(),
                                             get_count_formula()),
                jaccard=detail_description('Jaccard係数',
                                           jaccard_description(),
                                           get_jaccard_formula()),
                dice=detail_description('Dice係数',
                                        dice_description(),
                                        get_dice_formula()),
                simpson=detail_description('Simpson係数',
                                           simpson_description(),
                                           get_simpson_formula()),
                pmi=detail_description('相互情報量',
                                       pmi_description(),
                                       get_pmi_formula()),
                formula_description=detail_description('',
                                                       get_co_oc_formula_description(),
                                                       ''),
                sample=detail_table_description('例',
                                                co_oc_strength_sample_description(),
                                                pd.read_csv('csv/samples/co_oc_strength_result_sample.csv')))


def co_oc_strength_sample_description():
    """要検討"""
    description = r'<br>'.join(['『怪人二十面相』をJumanで分析し、それぞれの共起強度を「怪人二十面相」、「明智探偵」、「小林少年」、「中村」で比較した結果が以下の表です。',
                                'No.4の結果を見ると、Jaccard係数が0.009と極端に少なくなっています。これは、「中村」の出現頻度32よりも「怪人二十面相」の出現頻度543が極端に多いためです。',
                                'しかし、Simpson係数を見ると、0.156と高くなり、No.1の組み合わせよりもNo.4の組み合わせの方が関係が近いということになります。',
                                'No.5の結果を見ると、相互情報量が3.26と最も高く、No.2の組み合わせよりも低頻度で特殊な組み合わせであることが分かります。'])

    return description


def frequency_description():
    description = '<br>'.join(['最も単純で直感的な指標です。',
                               '他の計算法のような複雑な統計処理は施されておらず、指標としては最も粗いです。',
                               '機能語や句読記号などが上位に来ることが多いです。',
                               '通常の共起分析には利用されません。',
                               '値は0から文数の範囲を取ります。',
                               '値が大きいほど共通に登場した文が多く、2つの語は「近い」（類似度は高い）と判断します。',
                               '欠点として、統計処理が施されていないため、総語数の異なる作品で比較分析はできません。'])

    return description


def jaccard_description():
    description = '<br>'.join(['植物学者のPaul Jaccardによって考案された集合の類似度を測る指標です。',
                               '2集合に含まれている要素のうち共通要素が占める割合を表しています。',
                               '値は0から1の範囲を取ります。',
                               '値が大きいほど共通に登場した文が多く、2つの語は「近い」（類似度は高い）と判断します。',
                               '欠点としては、一方の集合だけ要素数が膨大である場合に類似度が著しく低下します。'])

    return description


def dice_description():
    description = '<br>'.join(['植物学者のThorvald SørensenとLee Raymond Diceによって考案された集合の類似度を測る指標です。',
                               '平均要素数と共通要素数の割合を表しています。',
                               'Jaccard係数の欠点である、一方の集合だけ要素数である場合に類似度が著しく低下する問題を防ぎ、共通要素数を重視した類似度計算です。',
                               '値は0から1の範囲を取ります。',
                               '値が大きいほど共通に登場した文が多く、2つの語は「近い」（類似度は高い）と判断します。',
                               '欠点としては、2集合の要素数に大きな差があり、差集合の要素数が膨大になった場合に類似度が低下します。'])

    return description


def simpson_description():
    description = '<br>'.join(['集合の類似度を測る指標です。',
                               '要素数が少ない方の要素数と共通要素数の割合を表しています。',
                               'Dice係数よりも差集合の要素数による影響を下げ、相対的に共通要素数を重視した類似度計算です。',
                               '値は0から1の範囲を取ります。',
                               '値が大きいほど共通に登場した文が多く、2つの語は「近い」（類似度は高い）と判断します。',
                               '欠点としては、一方の集合の要素数が少ない場合に、差集合の要素数がどれだけ多くても類似度がほとんど1となってしまいます。'])

    return description


def pmi_description():
    description = '<br>'.join(['低頻度の語を強調する傾向のある指標です。',
                               '値が2以上であると有意な組み合わせであるとされ、頻度は低いが特殊な組み合わせをうまく検出できます。',
                               '値は-∞から∞の範囲を取ります。'])

    return description
