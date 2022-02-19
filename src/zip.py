import zipfile
from src.get_data import get_datetime_now


def create_zip(zip_name: str, csv_data: dict, html_data: dict) -> str:
    """
    zipファイルの作成

    Parameters
    ----------
    zip_name: str
      作成するzipファイル名
    csv_data: dict
      zipに入れるcsvデータ, {'filename': 'arcname'}
    html_data: dict
      zipに入れるhtmlデータ, {'filename': 'arcname'}

    Returns
    -------
    zip_name: str
      zipを作成した時の名前
    time_now: str
      zipを作成した時の日付
    """

    # 作成時の日付を取得
    time_now = ''.join(get_datetime_now().split('_'))
    zip_name = f'{time_now}_{zip_name}'
    # zipファイルの作成
    with zipfile.ZipFile(f'tmp/{zip_name}.zip', 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for key, value in csv_data.items():
            zf.write(f'tmp/{key}.csv',
                     arcname=f'{value}_{time_now[:12]}.csv')
        for key, value in html_data.items():
            zf.write(f'tmp/{key}.html',
                     arcname=f'{value}_{time_now[:12]}.html')
    return zip_name, time_now
