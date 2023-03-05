from flask import Blueprint, send_from_directory, send_file
from src.zip import create_zip
from flask import redirect, url_for
from flask_limiter.util import get_remote_address
from flask_limiter import Limiter
from waitress import serve
import os
from route import app
from datetime import timedelta


UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# 16MBにデータ制限
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
# SECRET_KEYを設定
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
# ヘッダーにRateLimit情報を出力
app.config["RATELIMIT_HEADERS_ENABLED"] = True
# sessionの設定
app.permanent_session_lifetime = timedelta(minutes=30)
# アクセス制限
limiter = Limiter(app, key_func=get_remote_address, default_limits=["777 per minute"])


@app.errorhandler(404)
def not_found(error):
    return redirect(url_for("index.show"), code=200)


others_page = Blueprint("others", __name__)


@others_page.route("/dl/csv/<dl_type>/<target>/<new_name>", methods=["POST"])
@limiter.limit("7 per minute")
def download_csv(dl_type, target, new_name):
    """csvデータのダウンロード"""
    dir_path = f"csv/{dl_type.lower()}" if dl_type in ["khcoder", "Jumanpp", "MeCab"] else "tmp"
    return send_from_directory(
        dir_path,
        f"{target}.csv",
        as_attachment=True,
        attachment_filename=f"{new_name}.csv",
    )


@others_page.route("/dl/zip/<options_file>/<result_html>/<result_csv>/<new_name>", methods=["POST"])
@limiter.limit("7 per minute")
def download_zip(options_file, result_html, result_csv, new_name):
    """zipデータのダウンロード"""
    csv_data = {options_file: "設定項目", result_csv: "共起関係"}
    html_data = {result_html: "共起ネットワーク"}
    # zipの作成
    zip_name, time_now = create_zip(new_name, csv_data, html_data)
    download_name = f"{time_now[:12]}_設定と結果_{new_name}"
    return send_from_directory(
        "tmp",
        f"{zip_name}.zip",
        as_attachment=True,
        attachment_filename=f"{download_name}.zip",
    )


@others_page.route("/co-occurrence_network/visualization/<file_name>")
def show_co_oc_network(file_name):
    """共起ネットワーク用htmlファイル"""
    return send_file(f"tmp/{file_name}.html")


app.register_blueprint(others_page)


# おまじない
if __name__ == "__main__":
    serve(app)
