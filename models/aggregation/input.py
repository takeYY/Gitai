from src.aggregation import get_unique_hinshi_dict
from src.co_oc_network import get_csv_filename


class InputAggregation:
    """

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
    hinshi: dict
        入力データの品詞情報、品詞名: str -> 該当品詞の含有数: int
    errors: dict
        何らかの問題があったときのエラー情報
    """

    def __init__(self, request, session):
        form = request.form
        self.data_type: str = form.get('data_type',
                                       session.get('data_type'))
        self.mrph_type: str = form.get('mrph_type',
                                       session.get('mrph_type'))\
            if self.data_type == 'edogawa'\
            else ''
        self.set_input_name_csv(request, session)
        if not self.__dict__.get('errors'):
            # 品詞の辞書を設定
            self.set_hinshi()

    def set_input_name_csv(self, request, session):
        if session.get('input_name'):
            self.name: str = session.get('input_name')
            self.csv_name: str = session.get('input_csv_name')
        elif self.data_type == 'csv':
            (self.name,
             self.csv_name,
             self.errors) = get_csv_filename(request)
        else:
            self.name, self.csv_name = request.form.get('name').split('-')
        self.name = self.name.replace(' ', '')
        self.csv_name = self.csv_name.rsplit('.csv', 1)[0]

    def set_hinshi(self):
        self.hinshi: dict = get_unique_hinshi_dict(self.mrph_type,
                                                   self.csv_name)

    def set_errors(self, key: str, value: str):
        if not self.__dict__.get('errors'):
            self.errors = {}

        self.errors[key] = value

    def get_table_dict(self):
        return {'入力データタイプ': '江戸川乱歩作品' if self.data_type == 'edogawa' else 'CSVデータ',
                '入力データ名': self.name,
                '形態素解析器': 'MeCab' if self.data_type == 'edogawa' and self.mrph_type == 'mecab'
                else 'Jumanpp' if self.data_type == 'edogawa' and self.mrph_type == 'juman' else ''}

    def hinshi_sort(self):
        self.hinshi = dict(sorted(self.hinshi.items(),
                                  key=lambda x: x[1],
                                  reverse=True))
