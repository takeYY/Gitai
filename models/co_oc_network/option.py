from get_data import get_co_oc_strength_dict


class OptionCoOcNetwork:
    """
    設定画面の情報を保持する

    Attributes
    ----------
    dimension: int
        可視化する次元、[2, 3]
    co_oc_strength: str
        共起強度、['frequency', 'jaccard', 'dice', 'simpson', 'pmi']
    strength_max: float
        共起強度の最大値
    number: int
        表示する共起数上位
    hinshi_jpn: list of str
        日本語の品詞名
    selected_category: list of str
        選択されたカテゴリーのリスト
    remove_words: str
        ストップワード（表示しない単語）
    remove_combi: dict
        表示しない品詞の組み合わせ、1番目の品詞名: str -> 2番目の品詞名: dict
    target_words: str
        強制的に表示する単語
    synonym: str
        同義語（表記ゆれを1つの単語に集約）
    target_coef: str
        使用する共起強度の日本語名、['共起頻度', 'Jaccard係数', 'Dice係数', 'Simpson係数', '相互情報量']
    is_3d: bool
        3D表示を行うか否か
    errors: dict
        何らかの問題があったときのエラー情報
    """

    def __init__(self, request):
        form = request.form
        self.dimension: int = int(form.get('dimension'))
        self.co_oc_strength: str = form.get('co_oc_strength')
        self.strength_max: float = float(form.get('strength_max'))
        self.number: int = int(form.get('number'))
        self.hinshi_jpn: list = form.getlist('hinshi')
        self.selected_category: list = form.getlist('category')
        self.remove_words: str = form.get('remove-words')
        self.set_remove_combi(form)
        self.target_words: str = form.get('target-words')
        self.synonym: str = form.get('synonym')
        self.set_target_coef()
        self.is_3d: bool = self.set_is_3d()

    def set_remove_combi(self, form):
        remove_combi_meishi = form.getlist('remove-combi-meishi')
        remove_combi_doushi = form.getlist('remove-combi-doushi')
        remove_combi_keiyoushi = form.getlist('remove-combi-keiyoushi')
        remove_combi_fukushi = form.getlist('remove-combi-fukushi')
        self.remove_combi: dict = dict(meishi=remove_combi_meishi, doushi=remove_combi_doushi,
                                       keiyoushi=remove_combi_keiyoushi, fukushi=remove_combi_fukushi)

    def set_errors(self, key: str, value: str):
        if not self.__dict__.get('errors'):
            self.errors = {}

        self.errors[key] = value

    def set_target_coef(self):
        self.target_coef = get_co_oc_strength_dict().get(self.co_oc_strength, '共起頻度')

    def set_is_3d(self):
        return True if self.dimension == 3 else False

    def get_table_dict(self):
        return {'表示形式': '2D' if self.dimension == 2 else '3D',
                '共起数上位': self.number,
                '共起強度': self.target_coef,
                '共起強度の最大値': self.strength_max,
                '可視化対象の品詞': ', '.join(self.hinshi_jpn),
                'カテゴリー選択（3Dのみ）': ', '.join(self.selected_category) if self.selected_category else '',
                '指定ワード': ', '.join(self.target_words.split('\r\n')),
                '同義語指定': self.synonym,
                '除去ワード': ', '.join(self.remove_words),
                '除去対象の品詞組み合わせ（名詞）': ', '.join(self.remove_combi.get('meishi')),
                '除去対象の品詞組み合わせ（動詞）': ', '.join(self.remove_combi.get('doushi')),
                '除去対象の品詞組み合わせ（形容詞）': ', '.join(self.remove_combi.get('keiyoushi')),
                '除去対象の品詞組み合わせ（副詞）': ', '.join(self.remove_combi.get('fukushi'))}
