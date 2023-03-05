# Gitai

江戸川乱歩作品の分析アプリケーション

## 起動方法

`docker`，`docker-compose`コマンドが使えることを前提とする．

```bash
docker-compose up
```

## 環境変数

1. `app.example.env`をコピー

   ```bash
   cp app.example.env app.env
   ```

2. 内容を編集

   ```bash
   vim app.env
   ```

   ```env
   MODE="MAC"

   UPLOAD_FOLDER="/code/tmp"
   ALLOWED_EXTENSIONS={"csv"}
   SECRET_KEY=b"${your SECRET KEY}"

   M1MAC_MECAB_DICT_TARGET="-d /usr/lib/aarch64-linux-gnu/mecab/dic/mecab-ipadic-neologd"
   PROD_MECAB_DICT_TARGET="-d /usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd"
   ```

## SECRET_KEY の作成方法

```python
import os

os.urandom(24)
```

## URL

https://gitai.rampo.net/home

`Heroku`無料化に伴い以下は廃止

> https://rampo-edogawa-visualization.herokuapp.com/gitai/home
>
> 起動に 1 分ほどかかる．
