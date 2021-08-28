FROM python:3.7

# mecabとmecab-ipadic-NEologdの導入
RUN apt-get update \
  && apt-get install -y mecab \
  && apt-get install -y libmecab-dev \
  && apt-get install -y mecab-ipadic-utf8 \
  && apt-get install -y git \
  && apt-get install -y make \
  && apt-get install -y curl \
  && apt-get install -y xz-utils \
  && apt-get install -y file \
  && apt-get install -y sudo

RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git \
  && cd mecab-ipadic-neologd \
  && bin/install-mecab-ipadic-neologd -n -y

# Jumanppの導入
RUN wget https://github.com/ku-nlp/jumanpp/releases/download/v2.0.0-rc3/jumanpp-2.0.0-rc3.tar.xz \
  && apt-get install -y cmake \
  && apt-get install -y tar \
  && tar xJvf jumanpp-2.0.0-rc3.tar.xz \
  && cd jumanpp-2.0.0-rc3/ \
  && mkdir bld \
  && cd bld \
  && cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local \
  && sudo make install

# 日本語フォントの追加（noto）
RUN apt-get update \
  && apt-get -y install fonts-noto-cjk-extra \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir /code
WORKDIR /code

ADD . /code

RUN pip install --upgrade pip --no-cache-dir
RUN pip install -r requirements.txt --no-cache-dir
