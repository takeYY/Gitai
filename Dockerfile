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

RUN pip install mecab-python3==0.7

RUN mkdir /code
WORKDIR /code

ADD . /code

RUN pip install --upgrade pip --no-cache-dir
RUN pip install -r requirements.txt --no-cache-dir
