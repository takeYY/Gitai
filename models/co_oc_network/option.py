from src.get_data import get_co_oc_strength_dict


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
        表示する共起関係上位
    co_oc_freq_min: int
        共起頻度の最小値
    hinshi: list of str
        日本語の品詞名
    category: list of str
        選択されたカテゴリーのリスト
    remove_words: list of str
        ストップワード（表示しない単語）
    remove_combi: dict
        表示しない品詞の組み合わせ、1番目の品詞名: str -> 2番目の品詞名: dict
    target_words: list of str
        強制的に表示する単語群
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
        self.co_oc_freq_min: int = int(form.get('co_oc_freq_min'))
        self.hinshi: list = form.getlist('hinshi')
        self.category: list = form.getlist('category')
        self.remove_words: str = form.get('remove_words').split('\r\n')\
            if form.get('remove_words')\
            else []
        self.set_remove_combi(form)
        self.target_words: list = form.get('target_words').split('\r\n')\
            if form.get('target_words')\
            else []
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
        self.target_coef = get_co_oc_strength_dict().get(self.co_oc_strength, '共起頻度（0〜∞）')\
                                                    .split('（')[0]

    def set_is_3d(self):
        return True if self.dimension == 3 else False

    def get_table_dict(self):
        return {'表示形式': '2D' if self.dimension == 2 else '3D',
                '共起関係上位': self.number,
                '共起頻度の最小値': self.co_oc_freq_min,
                '共起強度': self.target_coef,
                '共起強度の最大値': self.strength_max,
                '可視化対象の品詞': ', '.join(self.hinshi),
                'カテゴリー選択（3Dのみ）': ', '.join(self.category) if self.category else '',
                '強制抽出語': ', '.join(self.target_words),
                '同義語指定': self.synonym,
                'ストップワード（強制除去語）': ', '.join(self.remove_words),
                '除去対象の品詞組み合わせ（名詞）': ', '.join(self.remove_combi.get('meishi')),
                '除去対象の品詞組み合わせ（動詞）': ', '.join(self.remove_combi.get('doushi')),
                '除去対象の品詞組み合わせ（形容詞）': ', '.join(self.remove_combi.get('keiyoushi')),
                '除去対象の品詞組み合わせ（副詞）': ', '.join(self.remove_combi.get('fukushi'))}
