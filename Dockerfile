FROM python:3.7

RUN mkdir /code
WORKDIR /code

ADD . /code

RUN pip install --upgrade pip --no-cache-dir
RUN pip install -r requirements.txt --no-cache-dir
