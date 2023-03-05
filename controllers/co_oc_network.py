from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.get_data import (
    get_basic_data,
    get_co_oc_strength_dict,
    get_novels_tuple,
    get_hinshi_dict,
    create_random_string,
)
from src.co_oc_network import create_network
from src.co_oc_3d_network import create_3d_network
from src.description import (
    categorization_description,
    csv_file_description,
    morphological_analysis_description,
    co_oc_strength_description,
)
from models.co_oc_network.input import InputCoOcNetwork
from models.co_oc_network.option import OptionCoOcNetwork
import pandas as pd


network_page = Blueprint("network", __name__, url_prefix="/co-oc-network")


def render_data_selection(basic_data: dict, edogawa_data: dict, description: dict, input_data: dict = None):
    return render_template(
        "co_oc_network/data_selection.html",
        basic_data=basic_data,
        edogawa_data=edogawa_data,
        description=description,
        input_data=input_data,
    )


def render_options(
    basic_data: dict,
    edogawa_data: dict,
    description: dict,
    input_data: InputCoOcNetwork,
    option: dict = None,
    co_oc_strength_dict: dict = get_co_oc_strength_dict(),
):
    return render_template(
        "co_oc_network/options.html",
        basic_data=basic_data,
        edogawa_data=edogawa_data,
        description=description,
        category_list=input_data.category_list,
        input_table=input_data.get_table_dict(),
        hinshi_dict=input_data.hinshi,
        option=option,
        co_oc_strength_dict=co_oc_strength_dict,
    )


def render_result(basic_data: dict, result_data: dict, dl_data: dict, input_data: dict, option: dict):
    return render_template(
        "co_oc_network/result.html",
        basic_data=basic_data,
        result_data=result_data,
        dl_data=dl_data,
        input_table=input_data,
        option_table=option,
    )


@network_page.route("/data-selection", methods=["GET"])
def data_selection():
    """
    共起ネットワーク
        データの選択画面
    """

    # 基本情報
    basic_data = get_basic_data(title="共起ネットワーク：データ選択", active_url="co_oc_network")
    # 形態素解析器の説明文
    description = dict(
        mrph=morphological_analysis_description(),
        categorization=categorization_description(),
        csv_sample=csv_file_description(),
    )
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(name_file=get_novels_tuple(col1="name", col2="file_name"))

    # セッションをクリア
    session.clear()
    return render_data_selection(basic_data, edogawa_data, description)


@network_page.route("/options", methods=["POST"])
def options():
    """
    共起ネットワーク
        設定画面
    """

    # 基本情報
    basic_data = get_basic_data(title="共起ネットワーク：設定画面", active_url="co_oc_network")
    # 形態素解析器の説明文
    description = dict(
        mrph=morphological_analysis_description(),
        categorization=categorization_description(),
        co_oc_strength=co_oc_strength_description(),
        csv_sample=csv_file_description(),
    )
    # 江戸川乱歩作品関連の情報
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(), name_file=get_novels_tuple(col1="name", col2="file_name"))
    # 入力データの設定
    input_data = InputCoOcNetwork(request, session)

    # セッション切れの場合
    if not input_data.data_type:
        session.clear()
        flash("セッションが切れました。再度データを選択してください。", "error")
        return render_data_selection(basic_data, edogawa_data, description)
    # errorがあれば
    if input_data.__dict__.get("errors"):
        return render_data_selection(basic_data, edogawa_data, description, input_data=input_data.__dict__)
    # 品詞がない場合
    if not input_data.hinshi:
        flash("品詞がありません。入力データの形式を確認してください。", "error")
        input_data.set_errors("csv_file_invalid", "品詞がありません。入力データの形式を確認してください。")
        return render_data_selection(basic_data, edogawa_data, description, input_data=input_data.__dict__)

    # sessionの登録
    session["data_type"] = input_data.data_type
    session["input_name"] = input_data.name
    session["input_csv_name"] = input_data.csv_name
    session["is_used_category"] = input_data.is_used_category
    session["mrph_type"] = input_data.mrph_type
    session["has_category"] = input_data.has_category_list()

    return render_options(basic_data, edogawa_data, description, input_data)


@network_page.route("/result", methods=["POST"])
def result():
    """
    共起ネットワーク
        結果表示画面
    """

    # 基本情報
    basic_data = get_basic_data(title="共起ネットワーク：結果画面", active_url="co_oc_network")
    # 形態素解析器の説明文
    description = dict(
        mrph=morphological_analysis_description(),
        categorization=categorization_description(),
        co_oc_strength=co_oc_strength_description(),
        csv_sample=csv_file_description(),
    )
    edogawa_data = dict(hinshi_dict=get_hinshi_dict(), name_file=get_novels_tuple(col1="name", col2="file_name"))
    # 入力データの形式
    input_data = InputCoOcNetwork(request, session)

    # セッション切れの場合
    if not input_data.data_type:
        session.clear()
        flash("セッションが切れました。再度データを選択してください。", "error")
        return render_data_selection(basic_data, edogawa_data, description)

    # 利用者から送られてきた情報の取得
    option = OptionCoOcNetwork(request)

    # 品詞が1つも選択されなかった場合
    if not option.hinshi:
        flash("「可視化対象の品詞」が1つも選択されていません。", "error")
        option.set_errors("hinshi", "品詞が選択されていません。")
    # 共起数が0以下だった場合
    if option.number < 1:
        flash("「共起関係上位」は1以上で設定してください。", "error")
        option.set_errors("number", "1以上で設定してください。")
    # 共起頻度の最小値が0以下だった場合
    if option.co_oc_freq_min < 1:
        flash("「共起頻度の最小値」は1以上で設定してください。", "error")
        option.set_errors("co_oc_freq_min", "1以上で設定してください。")
    # edogawa選択、カテゴリごとの表示選択、章がある作品において、チェックが一つもなかった場合
    if (
        input_data.data_type == "edogawa"
        and input_data.is_used_category
        and int(session.get("has_category"))
        and not option.category
    ):
        flash("「カテゴリー選択（3Dのみ）」が1つも選択されていません。", "error")
        option.set_errors("category", "カテゴリーが選択されていません。")
    # errorがあれば
    if option.__dict__.get("errors"):
        return render_options(basic_data, edogawa_data, description, input_data, option=option.__dict__)

    # 共起ネットワーク作成
    try:
        csv_file_name, co_oc_df = create_network(
            file_name=input_data.csv_name,
            target_hinshi=option.hinshi,
            target_num=option.number,
            remove_words=option.remove_words,
            remove_combi=option.remove_combi,
            target_words=option.target_words,
            data_type=input_data.data_type,
            is_used_3d=option.is_3d,
            used_category=input_data.is_used_category,
            synonym=option.synonym,
            selected_category=option.category,
            target_coef=option.target_coef,
            strength_max=option.strength_max,
            mrph_type=input_data.mrph_type,
            co_oc_freq_min=option.co_oc_freq_min,
            dimension=option.dimension,
        )
        if option.is_3d:
            html_file_name = create_3d_network(
                co_oc_df,
                target_num=option.number,
                used_category=input_data.is_used_category,
                category_list=option.category,
                target_coef=option.target_coef,
            )
        else:
            html_file_name = csv_file_name
    except Exception:
        import traceback

        traceback.print_exc()
        flash("ファイル形式が正しくありません。（入力形式に沿ってください）", "error")
        input_data.set_errors("csv_file_invalid", "ファイル形式が正しくありません。（入力形式に沿ってください）")
        return render_data_selection(basic_data, edogawa_data, description, input_data=input_data.__dict__)

    # 設定項目の保存
    options_filename = create_random_string(32)
    options_dict = dict(**input_data.get_table_dict(), **option.get_table_dict())
    pd.DataFrame(options_dict.items(), columns=["入力項目", "設定項目"]).to_csv(
        f"tmp/{options_filename}.csv", index=False, encoding="utf_8_sig"
    )

    # データダウンロード設定
    dl_data = dict(
        file_name=csv_file_name,
        dl_type="result",
        new_name=f'{input_data.name}_{"-".join(option.hinshi)}_{option.number}',
        options_filename=options_filename,
    )
    # 結果情報を格納
    result_data = dict(file_name=csv_file_name, html_file_name=html_file_name, co_oc_df=co_oc_df[: option.number])

    try:
        return render_result(basic_data, result_data, dl_data, input_data.get_table_dict(), option.get_table_dict())
    except Exception:
        return redirect(url_for("network.data_selection"))


@network_page.route("/full_screen/<target>", methods=["POST"])
def full_screen(target):
    # 基本情報
    basic_data = get_basic_data(title="共起ネットワーク：結果全画面", active_url="co_oc_network")
    return render_template("co_oc_network/full_screen.html", basic_data=basic_data, target=target)
