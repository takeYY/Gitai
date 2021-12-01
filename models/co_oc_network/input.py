from aggregation import get_unique_hinshi_dict
from co_oc_network import get_csv_filename
from get_data import get_category_list


class InputCoOcNetwork:
    """
    データ選択画面の情報を保持する

    Attributes
    ----------
    data_type: str
        入力データの形式、['edogawa', 'csv']
    mrph_type: str
        使用する形態素解析器（data_typeが'edogawa'の場合）、['mecab', 'juman']
    name: str
        入力データの名前
    csv_name: str
        csvデータのファイル名
    is_used_category: int
        カテゴリごとの表示を行う(1)か否(0)か
    hinshi: dict
        入力データの品詞情報、品詞名: str -> 該当品詞の含有数: int
    category_list: list of str
        カテゴリーのリスト
    errors: dict
        何らかの問題があったときのエラー情報
    """

    def __init__(self, request, session):
        form = request.form
        self.data_type: str = form.get('data_type',
                                       session.get('data_type'))
        self.mrph_type: str = form.get('mrph',
                                       session.get('mrph_type'))\
            if self.data_type == 'edogawa'\
            else ''
        self.set_input_name_csv(request, session)
        # カテゴリごとの表示有無
        self.is_used_category: int = int(form.get('is_used_category',
                                                  session.get('is_used_category', 0)))
        if not self.__dict__.get('errors'):
            # 品詞の辞書を設定
            self.set_hinshi()
            # カテゴリごとの表示を希望する場合
            self.set_category_list()

    def set_input_name_csv(self, request, session):
        form = request.form
        if session.get('input_name'):
            self.name: str = session.get('input_name')
            self.csv_name: str = session.get('input_csv_name')
        elif self.data_type == 'csv':
            (self.name,
             self.csv_name,
             self.errors) = get_csv_filename(request)
        else:
            self.name, self.csv_name = form.get('name').split('-')
        self.name = self.name.replace(' ', '')
        self.csv_name = self.csv_name.rsplit('.csv', 1)[0]

    def set_hinshi(self):
        self.hinshi: dict = get_unique_hinshi_dict(self.mrph_type,
                                                   self.csv_name)

    def set_category_list(self):
        self.category_list: list = get_category_list(self.csv_name)\
            if self.is_used_category == 1\
            else []

    def set_errors(self, key: str, value: str):
        if not self.__dict__.get('errors'):
            self.errors = {}

        self.errors[key] = value

    def get_table_dict(self):
        return {'入力データタイプ': '江戸川乱歩作品' if self.data_type == 'edogawa' else 'CSVデータ',
                '入力データ名': self.name,
                '章ごとのカテゴリ分割': 'する' if self.is_used_category == 1 else 'しない',
                '形態素解析器': 'MeCab' if self.data_type == 'edogawa' and self.mrph_type == 'mecab'
                else 'Jumanpp' if self.data_type == 'edogawa' and self.mrph_type == 'juman' else ''}

    def has_category_list(self):
        if not self.category_list or self.category_list and self.category_list[0] == '< 章なし >':
            return 0

        return 1

    def hinshi_sort(self):
        self.hinshi = dict(sorted(self.hinshi.items(),
                                  key=lambda x: x[1],
                                  reverse=True))
