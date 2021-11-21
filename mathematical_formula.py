def get_count_formula():
    formula = r"""\begin{align}
      共起回数=|A\cap B|
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
