import pandas as pd
from src.mathematical_formula import (
    get_count_formula,
    get_jaccard_formula,
    get_dice_formula,
    get_simpson_formula,
    get_pmi_formula,
    get_co_oc_formula_description,
)


def list2str_with_br(description: list):
    return "<br>".join(description)


# 詳細説明を文章と数式で行う場合のHTMLタグ構成
def detail_description(title: str = None, description: str = None, formula: str = None) -> str:
    html_text = ""
    if title:
        html_text += rf"""<h5>{title}</h5>"""
    if description:
        html_text += rf"""<p class='px-2 small'>{description}</p>"""
    if formula:
        html_text += rf"""<div class='text-center'>{formula}</div>"""

    return html_text


# 詳細説明を文章と表で行う場合のHTMLタグ構成
def detail_table_description(
    title: str = None, description: str = None, table: pd.DataFrame = None, has_index: bool = False
) -> str:
    html_text = ""
    if title:
        html_text += rf"""<h5>{title}</h5>"""
    if description:
        html_text += rf"""<p class='px-2 small'>{description}</p>"""
    if table is not None:
        html_text += r"""<div class='p-2 small table-responsive'>
                            <table class='table table-hover table-striped table-sm'>
                                <thead class='thead-dark'>
                                    <tr>"""
        if has_index:
            html_text += r"""<th></th>"""
        for column in table.columns:
            html_text += rf"""<th scope='col'>{column}</th>"""
        html_text += r"""</tr></thead><tbody>"""
        for idx, rows in table.iterrows():
            html_text += r"""<tr>"""
            if has_index:
                html_text += rf"""<th>{idx}</th>"""
            for column in table.columns:
                html_text += rf"""<th>{rows[column]}</th>"""
            html_text += r"""</tr>"""
        html_text += r"""</tbody></table></div>"""

    return html_text


# 詳細説明を文章と図で行う場合のHTMLタグ構成
def detail_image_description(title: str = None, description: str = None, images: dict = None):
    html_text = ""
    if title:
        html_text += rf"""<h5>{title}</h5>"""
    if description:
        html_text += rf"""<p class='px-2 small'>{description}</p>"""
    if images is not None:
        html_text += r"""<div class='p-2'>"""
        if images.get("comparison") and len(images.get("images", [])) == 2:
            html_text += r"""<div class='row'>
                                <div class='col-md-5'>
                                    <div class='card'>
                                        <img src={images.get('images')[0]}>
                                    </div>
                                </div>
                                <div class='col-md-1 h2 d-flex align-items-center justify-content-center'>
                                    >
                                </div>
                                <div class='col-md-5'>
                                    <div class='card'>
                                        <img src={images.get('images')[1]}>
                                    </div>
                                </div>
                            </div>"""
        else:
            html_text += r"""<div class='row'>"""
            for image in images.get("images", []):
                html_text += rf"""<div class='col-md-3'>
                                    <div class='card'>
                                        <img src={image}>
                                    </div>
                                </div>"""
            html_text += r"""</div>"""
        html_text += r"""</div>"""
    return html_text


def csv_file_description():
    return dict(
        sample1=detail_table_description("サンプルデータ1（MeCab）", "", pd.read_csv("csv/samples/input_csv_sample1.csv")),
        sample2=detail_table_description("サンプルデータ2（Jumanpp）", "", pd.read_csv("csv/samples/input_csv_sample2.csv")),
    )


def morphological_analysis_description():
    return dict(
        mecab=detail_description("MeCab", mecab_description()),
        neologd=detail_description("NEologd", neologd_description()),
        juman=detail_description("Jumanpp", juman_description()),
        sample1_mecab=detail_table_description(
            "サンプル1：「外国人参政権」の解析結果", "MeCab（NEologd）の出力例", pd.read_csv("csv/samples/mecab_sample1.csv")
        ),
        sample1_juman=detail_table_description("", "Jumanppの出力例", pd.read_csv("csv/samples/juman_sample1.csv")),
        sample2_mecab=detail_table_description(
            "サンプル2：「うらにわにはにわ、にわにはにわとりがいる。」の解析結果", "MeCab（NEologd）の出力例", pd.read_csv("csv/samples/mecab_sample2.csv")
        ),
        sample2_juman=detail_table_description("", "Jumanppの出力例", pd.read_csv("csv/samples/juman_sample2.csv")),
    )


def categorization_description():
    image_options = dict(
        comparison=True,
        images=[
            "https://raw.githubusercontent.com/takeYY/Rampo_Edogawa_Visualization/"
            + "main/static/images/network_3D.png",
            "https://raw.githubusercontent.com/takeYY/Rampo_Edogawa_Visualization/"
            + "main/static/images/network_3D_categorization.png",
        ],
    )
    return detail_image_description("章ごとのカテゴリ分割", is_used_category_description(), image_options)


def co_oc_strength_description():
    return dict(
        jaccard=detail_description("Jaccard係数", jaccard_description(), get_jaccard_formula()),
        dice=detail_description("Dice係数", dice_description(), get_dice_formula()),
        simpson=detail_description("Simpson係数", simpson_description(), get_simpson_formula()),
        frequency=detail_description("共起頻度", frequency_description(), get_count_formula()),
        pmi=detail_description("相互情報量", pmi_description(), get_pmi_formula()),
        formula_description=detail_description("", get_co_oc_formula_description(), ""),
        sample=detail_table_description(
            "例", co_oc_strength_sample_description(), pd.read_csv("csv/samples/co_oc_strength_result_sample.csv")
        ),
    )


def preprocessing_other_options_description():
    return dict(
        all2half=detail_table_description(
            "全角を半角へ変換", "", pd.read_csv("csv/samples/all2half_description.csv").T, has_index=True
        ),
        big2small=detail_table_description("英語大文字を小文字へ変換", "例文", pd.read_csv("csv/samples/big2small.csv")),
        remove_symbols=detail_table_description(
            "記号を削除", "", pd.read_csv("csv/samples/remove_symbols_description.csv").T, has_index=True
        ),
        replace_numbers2zero=detail_table_description(
            "数字を全て0に変換", "例文", pd.read_csv("csv/samples/replace_numbers2zero.csv")
        ),
    )


def is_used_category_description():
    description = ["次ページの表示形式で3Dを選択すると対象データを時系列として分析できます。", "章ごとに共起関係を可視化したい場合に有効です。"]

    return list2str_with_br(description)


def co_oc_strength_sample_description():
    description = [
        "『怪人二十面相』をJumanで分析し、それぞれの共起強度を「怪人二十面相」、「明智探偵」、「小林少年」、「中村」で比較した結果が以下の表です。",
        "No.4の結果を見ると、Jaccard係数が0.009と極端に少なくなっています。これは、「中村」の出現頻度32よりも「怪人二十面相」の出現頻度543が極端に多いためです。",
        "しかし、Simpson係数を見ると、0.156と高くなり、No.1の組み合わせよりもNo.4の組み合わせの方が関係が近いということになります。",
        "No.5の結果を見ると、相互情報量が3.26と最も高く、No.2の組み合わせよりも低頻度で特殊な組み合わせであることが分かります。",
    ]

    return list2str_with_br(description)


def mecab_description():
    description = ["高速に解析ができ、日本語テキストの中では最もよく使われています。", "とりあえず解析したい場合は、MeCabを選択すると良いでしょう。"]

    return list2str_with_br(description)


def neologd_description():
    description = ["MeCabの解析時に使用する辞書のことで、辞書の更新を頻繁に行っています。", "そのため、新語・固有名詞の解析が得意で語彙数も多いです。"]

    return list2str_with_br(description)


def juman_description():
    description = ["MeCabよりも高精度で単語の分割、品詞の判別が可能です。", "ただし、欠点として解析に時間がかかり、単語の分割が細かいことが挙げられます。"]

    return list2str_with_br(description)


def frequency_description():
    description = [
        "最も単純で直感的な指標です。",
        "他の計算法のような複雑な統計処理は施されておらず、指標としては最も粗いです。",
        "機能語や句読記号などが上位に来ることが多いです。",
        "通常の共起分析には利用されません。",
        "値は0から文数の範囲を取ります。",
        "値が大きいほど共通に登場した文が多く、2つの語は「近い」（類似度は高い）と判断します。",
        "欠点として、統計処理が施されていないため、総語数の異なる作品で比較分析はできません。",
    ]

    return list2str_with_br(description)


def jaccard_description():
    description = [
        "植物学者のPaul Jaccardによって考案された集合の類似度を測る指標です。",
        "2集合に含まれている要素のうち共通要素が占める割合を表しています。",
        "値は0から1の範囲を取ります。",
        "値が大きいほど共通に登場した文が多く、2つの語は「近い」（類似度は高い）と判断します。",
        "欠点としては、一方の集合だけ要素数が膨大である場合に類似度が著しく低下します。",
    ]

    return list2str_with_br(description)


def dice_description():
    description = [
        "植物学者のThorvald SørensenとLee Raymond Diceによって考案された集合の類似度を測る指標です。",
        "平均要素数と共通要素数の割合を表しています。",
        "Jaccard係数の欠点である、一方の集合だけ要素数である場合に類似度が著しく低下する問題を防ぎ、共通要素数を重視した類似度計算です。",
        "値は0から1の範囲を取ります。",
        "値が大きいほど共通に登場した文が多く、2つの語は「近い」（類似度は高い）と判断します。",
        "欠点としては、2集合の要素数に大きな差があり、差集合の要素数が膨大になった場合に類似度が低下します。",
    ]

    return list2str_with_br(description)


def simpson_description():
    description = [
        "集合の類似度を測る指標です。",
        "要素数が少ない方の要素数と共通要素数の割合を表しています。",
        "Dice係数よりも差集合の要素数による影響を下げ、相対的に共通要素数を重視した類似度計算です。",
        "値は0から1の範囲を取ります。",
        "値が大きいほど共通に登場した文が多く、2つの語は「近い」（類似度は高い）と判断します。",
        "欠点としては、一方の集合の要素数が少ない場合に、差集合の要素数がどれだけ多くても類似度がほとんど1となってしまいます。",
    ]

    return list2str_with_br(description)


def pmi_description():
    description = ["低頻度の語を強調する傾向のある指標です。", "値が2以上であると有意な組み合わせであるとされ、頻度は低いが特殊な組み合わせをうまく検出できます。", "値は-∞から∞の範囲を取ります。"]

    return list2str_with_br(description)
