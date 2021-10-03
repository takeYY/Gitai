from flask import redirect, url_for
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
# sessionの設定
app.permanent_session_lifetime = timedelta(minutes=30)


@app.errorhandler(404)
def not_found(error):
    return redirect(url_for('index.show'), code=200)


# おまじない
if __name__ == "__main__":
    serve(app)
