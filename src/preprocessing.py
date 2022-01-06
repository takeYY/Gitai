import re
import string


def get_other_option_dict():
    return dict(all2half='全角を半角へ変換', big2small='英語大文字を小文字へ変換', remove_symbols='記号を削除', replace_numbers2zero='数字を全て0に変換')


def texts_preprocessing(texts: str, remove_words, remove_word_in_texts, replace_words, other_options):
    """
    テキストの前処理

    Parameters
    ----------
    texts: str
        入力テキスト
    remove_words: str
        削除設定の文字列
    remove_word_in_texts: str
        指定文字列とその中身の削除設定の文字列
    replace_words: str
        置換設定の文字列
    other_options: list of str
        その他設定

    Returns
    -------
    result: str
        前処理された文字列
    errors: dict
        前処理でエラーとなった情報
    """
    # テキストを前処理
    preprocessed_text = []
    # エラーの有無
    errors = {}
    for text in texts.split('\r\n'):
        if errors:
            break

        if remove_words:
            for rw in remove_words.split('\r\n'):
                text = text.replace(rw, '')
        if remove_word_in_texts:
            for rwit in remove_word_in_texts.split('\r\n'):
                try:
                    alpha, omega = rwit.split(',')
                    text = re.sub(f'\{alpha}.*?\{omega}', '', text)
                except:
                    errors['remove_text_in_texts'] = '「指定文字列とその中身の削除設定」の入力形式が違います。'
                    break
        if replace_words:
            for rw in replace_words.split('\r\n'):
                try:
                    target, replace = rw.split(' ')
                    text = text.replace(target, replace)
                except:
                    errors['replace_texts'] = '「置換設定」の入力形式が違います。'
                    break
        # エラーがある場合、処理終了
        if errors:
            return '', errors
        # 全角 => 半角
        if 'all2half' in other_options:
            text = text.translate(str.maketrans(
                {chr(0xFF01 + i): chr(0x21 + i) for i in range(94)}))
        # 英語大文字を小文字化
        if 'big2small' in other_options:
            text = text.lower()
        # 記号を削除（半角スペースに置換後、半角スペースで結合）
        if 'remove_symbols' in other_options:
            table = str.maketrans(string.punctuation,
                                  ' '*len(string.punctuation))
            text = ' '.join(text.translate(table).split())
        # 数字列を0に置換
        if 'replace_numbers2zero' in other_options:
            text = re.sub('[0-9]+', '0', text)
        preprocessed_text.append(text)

    result = '\r\n'.join(preprocessed_text)

    return result, errors
