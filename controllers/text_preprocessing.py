from flask import Blueprint, render_template, request, flash
from src.description import preprocessing_other_options_description
from src.get_data import get_basic_data
from src.preprocessing import texts_preprocessing, get_other_option_dict

preprocessing_page = Blueprint("text_preprocessing", __name__, url_prefix="/text-preprocessing")


def render_index(basic_data: dict, other_option: dict, description: dict, input_data: dict = None, option: dict = None):
    return render_template(
        "text_preprocessing/index.html",
        basic_data=basic_data,
        other_option=other_option,
        description=description,
        input_data=input_data,
        option=option,
    )


def render_result(
    basic_data: dict,
    other_option: dict,
    description: dict,
    input_data: dict = None,
    option: dict = None,
    result: dict = None,
):
    return render_template(
        "text_preprocessing/index.html",
        basic_data=basic_data,
        other_option=other_option,
        description=description,
        input_data=input_data,
        option=option,
        result=result,
    )


@preprocessing_page.route("", methods=["GET", "POST"])
def show():
    """
    テキストの前処理

    """
    # 基本情報
    basic_data = get_basic_data(title="テキストの前処理", active_url="preprocessing")
    # その他設定の項目取得
    other_option = get_other_option_dict()
    # 詳細説明追加
    description = dict(other_options=preprocessing_other_options_description())
    if request.method == "GET":
        return render_index(basic_data, other_option, description)

    # 利用者から送られてきた情報を取得
    texts = request.form.get("texts")
    # textsがない場合
    if not texts:
        flash("テキストが入力されていません。", "error")
        error = dict(texts="テキストが入力されていません。")
        return render_index(basic_data, other_option, description, dict(errors=error))
    input_data = dict(texts=texts)

    remove_words = request.form["remove_texts"]
    remove_word_in_texts = request.form["remove_text_in_texts"]
    replace_words = request.form["replace_texts"]
    other_options = request.form.getlist("other_option")
    # 選択されたその他設定を取得
    selected_option = [other_option.get(k) for k in other_options]
    # 送られてきた情報を基にテキストを前処理
    preprocessed_text, errors = texts_preprocessing(
        texts, remove_words, remove_word_in_texts, replace_words, other_options
    )
    # 送るデータの辞書
    option = dict(
        remove_texts=remove_words,
        replace_texts=replace_words,
        remove_text_in_texts=remove_word_in_texts,
        other_option=selected_option,
    )
    # エラーがある場合
    if errors:
        for error in errors.values():
            flash(error, "error")
        option["errors"] = errors
        return render_index(basic_data, other_option, description, input_data, option)
    # 送るデータをまとめる
    result = dict(preprocessed_texts=preprocessed_text)
    return render_result(basic_data, other_option, description, input_data, option, result)
