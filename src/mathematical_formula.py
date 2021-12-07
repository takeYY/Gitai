def get_count_formula():
    formula = r"""\begin{align}
      共起頻度=|A\cap B|
      \end{align}"""
    return formula


def get_jaccard_formula():
    formula = r"""\begin{align}
      Jaccard係数=\frac{|A\cap B|}{|A\cup B|}
      \end{align}"""
    return formula


def get_dice_formula():
    formula = r"""\begin{align}
      Dice係数=\frac{2|A\cap B|}{|A|+|B|}
      \end{align}"""
    return formula


def get_simpson_formula():
    formula = r"""\begin{align}
      Simpson係数=\frac{|A\cap B|}{min(|A|,|B|)}
      \end{align}"""
    return formula


def get_pmi_formula():
    formula = r"""\begin{align}
      相互情報量=\log_2\frac{|A\cap B|\times N}{|A|\times|B|}
      \end{align}"""
    return formula


def get_co_oc_formula_description():
    formula = r"""\begin{align}
      A&：単語aの集合\\
      B&：単語bの集合\\
      |A\cup B|&：AとBの和集合の要素数\\
      |A|&：Aの要素数\\
      |B|&：Bの要素数\\
      min(|A|,|B|)&：AとBの要素数の中から最小値\\
      N&：総語数
    \end{align}"""

    return formula
