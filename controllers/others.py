from flask import Blueprint, request, send_from_directory, send_file


others_page = Blueprint('others', __name__)


@others_page.route('/download/csv', methods=['POST'])
def download_csv():
    """
    csvデータのダウンロード

    """
    dir_path = request.form.get('dir_path')
    file_name = request.form.get('file_name')
    new_name = request.form.get('new_name')

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
