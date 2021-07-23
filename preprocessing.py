import re
import string


def get_other_option_dict():
    return dict(all2half='全角を半角へ変換', big2small='英語大文字を小文字へ変換', remove_symbols='記号を削除', replace_numbers='数字を全て0に変換')


def get_other_option_description_dict():
    description = ["""変換対象：！＂＃＄％＆＇（）＊＋，－．／０１２３４５６７８９：；＜＝＞？＠ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ［＼］＾＿｀ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ｛｜｝～
  変換後：!"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~""",
                   """Hi, can you hear me? ==> hi, can you hear me?
  Ｈｅｌｌｏ ==> ｈｅｌｌｏ""",
                   """削除対象：!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~""",
                   """明治27年10月21日 ==> 明治0年0月0日"""]
    return {value: description[idx] for idx, value in enumerate(get_other_option_dict().values())}


def texts_preprocessing(texts, remove_words, replace_words, other_options):
    # テキストを前処理
    preprocessed_text = []
    for text in texts.split('\r\n'):
        if remove_words:
            for rw in remove_words.split('\r\n'):
                text = text.replace(rw, '')
        if replace_words:
            for rw in replace_words.split('\r\n'):
                try:
                    target, replace = rw.split(' ')
                    text = text.replace(target, replace)
                except:
                    continue
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
        if 'replace_numbers' in other_options:
            text = re.sub('[0-9]+', '0', text)
        preprocessed_text.append(text)

    return preprocessed_text
