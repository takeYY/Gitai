from flask import Blueprint, send_from_directory, send_file
from src.get_data import get_datetime_now
import zipfile
from flask import redirect, url_for
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from waitress import serve
import os
from route import app
from datetime import timedelta


UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 16MBにデータ制限
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# SECRET_KEYを設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
# ヘッダーにRateLimit情報を出力
app.config['RATELIMIT_HEADERS_ENABLED'] = True
# sessionの設定
app.permanent_session_lifetime = timedelta(minutes=30)
# アクセス制限
limiter = Limiter(app, key_func=get_remote_address,
                  default_limits=['10 per minute'])


@app.errorhandler(404)
def not_found(error):
    return redirect(url_for('index.show'), code=200)


others_page = Blueprint('others', __name__)


@others_page.route('/gitai/dl/csv/<dl_type>/<target>/<new_name>', methods=['POST'])
@limiter.limit('1 per minute')
def download_csv(dl_type, target, new_name):
    """csvデータのダウンロード"""
    if dl_type == 'khcoder':
        dir_path = 'csv/khcoder'
    elif dl_type == 'Jumanpp':
        dir_path = 'csv/jumanpp'
    elif dl_type == 'MeCab':
        dir_path = 'csv/mecab_with_category'
    else:
        dir_path = 'tmp'
    return send_from_directory(dir_path,
                               f'{target}.csv',
                               as_attachment=True,
                               attachment_filename=f'{new_name}.csv',)


@others_page.route('/gitai/dl/zip/<options_file>/<result_html>/<result_csv>/<new_name>', methods=['POST'])
@limiter.limit('1 per minute')
def download_zip(options_file, result_html, result_csv, new_name):
    """zipデータのダウンロード"""
    time_now = ''.join(get_datetime_now().split('_'))
    zip_name = f'{time_now}_{new_name}'
    download_name = f'{time_now[:12]}_設定と結果_{new_name}'
    # zipの作成
    with zipfile.ZipFile(f'tmp/{zip_name}.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        zf.write(f'tmp/{options_file}.csv',
                 arcname=f'設定項目_{time_now[:12]}.csv')
        zf.write(f'tmp/{result_html}.html',
                 arcname=f'共起ネットワーク_{time_now[:12]}.html')
        zf.write(f'tmp/{result_csv}.csv',
                 arcname=f'共起関係_{time_now[:12]}.csv')
    return send_from_directory(
        'tmp',
        f'{zip_name}.zip',
        as_attachment=True,
        attachment_filename=f'{download_name}.zip',
    )


@others_page.route('/gitai/co-occurrence_network/visualization/<file_name>')
def show_co_oc_network(file_name):
    """共起ネットワーク用htmlファイル"""
    return send_file(f'tmp/{file_name}.html')


app.register_blueprint(others_page)


# おまじない
if __name__ == "__main__":
    serve(app)
