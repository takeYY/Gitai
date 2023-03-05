from flask import Blueprint, render_template
from src.get_data import get_basic_data, get_edogawa_merge_df

information_page = Blueprint("information", __name__, url_prefix="/information")


@information_page.route("")
def show():
    """作品情報"""

    # 基本情報
    basic_data = get_basic_data(title="作品情報", active_url="information")
    # 江戸川乱歩作品関連の情報
    edogawa_merge_df = get_edogawa_merge_df(drop_duplicates=True)

    return render_template(
        "information/index.html",
        basic_data=basic_data,
        edogawa_merge_df=edogawa_merge_df,
        mrphs=["MeCab", "Jumanpp"],
    )
