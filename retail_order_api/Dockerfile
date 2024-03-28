FROM python:3.12-alpine

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERD 1

COPY requirements.txt /usr/src/app/requirements.txt

RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY . /usr/src/app
