from flask import Blueprint, render_template
from src.get_data import get_basic_data

index_page = Blueprint('index', __name__, url_prefix='/gitai/home')


@index_page.route('')
def show():
    """
    ホーム

    """
    # 基本情報
    basic_data = get_basic_data()

    return render_template('index.html', basic_data=basic_data)
