from get_data import get_co_oc_strength_dict


class OptionAggregation:
    """
    設定画面の情報を保持する

    Attributes
    ----------
    hinshi_jpn: list of str
        日本語の品詞名
    errors: dict
        何らかの問題があったときのエラー情報
    """

    def __init__(self, request):
        form = request.form
        self.hinshi_jpn: list = form.getlist('hinshi')

    def set_errors(self, key: str, value: str):
        if not self.__dict__.get('errors'):
            self.errors = {}

        self.errors[key] = value

    def get_table_dict(self):
        return {'可視化対象の品詞': ', '.join(self.hinshi_jpn)}
