# Gitai

江戸川乱歩作品の分析アプリケーション

## 起動方法

`docker`，`docker-compose`コマンドが使えることを前提とする．

```bash
docker-compose up
```

## 環境変数

- app.env
  ```env
  UPLOAD_FOLDER="/code/tmp"
  ALLOWED_EXTENSIONS={"csv"}
  SECRET_KEY=b"${your SECRET KEY}"
  ```

## SECRET_KEY の作成方法

```python
import os

os.urandom(24)
```

## URL

https://gitai.rampo.net/home

`Heroku`無料化に伴い廃止

> https://rampo-edogawa-visualization.herokuapp.com/gitai/home
>
> 起動に 1 分ほどかかる．
