from flask import Blueprint, request, render_template, send_from_directory, send_file, session
from get_data import get_basic_data


others_page = Blueprint('others', __name__)


@others_page.route('/download/csv', methods=['POST'])
def download_csv():
    """
    csvデータのダウンロード

    """
    dir_path = session.get('dir_path')
    file_name = session.get('file_name')
    new_name = session.get('new_name')

    # sessionが切れた場合
    if not file_name:
        # 基本情報
        basic_data = get_basic_data(
            title='セッション切れ', active_url='session_timeout_error')
        return render_template('session_timeout.html', basic_data=basic_data)

    return send_from_directory(
        dir_path,
        f'{file_name}.csv',
        as_attachment=True,
        attachment_filename=f'{new_name}.csv',
    )


@others_page.route('/co-occurrence_network/visualization/<file_name>')
def show_co_oc_network(file_name):
    """
    共起ネットワーク用htmlファイル

    """
    return send_file(f'tmp/{file_name}.html')
