# Rampo-Edogawa-Visualization
江戸川乱歩作品の作品分析ページ

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

## SECRET_KEYの作成方法
```python
import os

os.urandom(24)
```

## URL
https://rampo-edogawa-visualization.herokuapp.com/gitai/home

起動に1分ほどかかる．
