from flask import Blueprint, render_template, request, flash, session
from src.description import categorization_description, csv_file_description, morphological_analysis_description
from src.get_data import get_basic_data, save_df
from src.morphological import mrph_analysis

morph_analysis_page = Blueprint("morph_analysis", __name__, url_prefix="/morphological-analysis")


def render_index(basic_data: dict, description: dict, option: dict = None):
    return render_template(
        "morphological_analysis/index.html",
        basic_data=basic_data,
        description=description,
        option=option,
    )


def render_result(basic_data: dict, description: dict, option: dict = None, result: dict = None):
    return render_template(
        "morphological_analysis/index.html",
        basic_data=basic_data,
        description=description,
        option=option,
        result=result,
    )


@morph_analysis_page.route("", methods=["GET", "POST"])
def show():
    """形態素解析"""

    # 基本情報
    basic_data = get_basic_data(title="形態素解析", active_url="morph_analysis")
    # 形態素解析器の説明文
    description = dict(
        mrph=morphological_analysis_description(),
        categorization=categorization_description(),
        csv_sample=csv_file_description(),
    )

    # リクエストがGETならば
    if request.method == "GET":
        session.clear()
        return render_index(basic_data, description)

    # 送信されたデータの取得と形態素解析器の種類
    text = request.form.get("words")
    mrph_type = request.form.get("mrph_type")

    # テキストが入力されなかった場合
    if not text:
        flash("テキストが入力されていません。", "error")
        return render_index(basic_data, description)

    option = dict(text=text, mrph_type=mrph_type)
    # 形態素解析
    mrph_df = mrph_analysis(mrph_type, text)

    # 形態素解析の結果が返ってこなかった場合
    if mrph_df.empty:
        flash("解析に失敗しました。テキストデータが大きすぎます。", "error")
        return render_index(basic_data, description, option)

    # mrph_dfをcsvとして保存し、csv_nameを取得
    csv_name = save_df(mrph_df)
    # 結果のデータ群
    result = dict(df=mrph_df, file_name=csv_name, dl_type="result", new_name=f"{mrph_type}による形態素解析結果")

    return render_result(basic_data, description, option, result)
