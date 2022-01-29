from flask import Blueprint, request, render_template, send_from_directory, send_file, session
from src.get_data import get_basic_data


others_page = Blueprint('others', __name__)


@others_page.route('/rikkyo-edogawa/dl/csv/<dl_type>/<target>/<new_name>', methods=['POST'])
def download_csv(dl_type, target, new_name):
    """
    csvデータのダウンロード

    """
    if dl_type == 'khcoder':
        dir_path = 'csv/khcoder'
    elif dl_type == 'Jumanpp':
        dir_path = 'csv/jumanpp'
    elif dl_type == 'MeCab':
        dir_path = 'csv/mecab_with_category'
    else:
        dir_path = 'tmp'
    return send_from_directory(
        dir_path,
        f'{target}.csv',
        as_attachment=True,
        attachment_filename=f'{new_name}.csv',
    )


@others_page.route('/rikkyo-edogawa/co-occurrence_network/visualization/<file_name>')
def show_co_oc_network(file_name):
    """
    共起ネットワーク用htmlファイル

    """
    return send_file(f'tmp/{file_name}.html')
