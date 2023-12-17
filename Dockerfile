FROM python:3.9-alpine3.14

USER root

RUN apk add --no-cache ffmpeg bzip2 libpq postgresql-client\
    && apk add --no-cache --virtual .build-deps make jpeg-dev zlib-dev musl-dev gcc g++ libffi-dev postgresql-dev

ARG ZOU_VERSION

COPY ./requirements.txt /opt/zou/requirements.txt
COPY ./setup.py /opt/zou/setup.py
COPY ./setup.cfg /opt/zou/setup.cfg

WORKDIR /opt/zou
RUN pip install -r requirements.txt

COPY . /opt/zou

RUN pip install --upgrade pip wheel setuptools
RUN pip install .
RUN apk del .build-deps

ENV ZOU_FOLDER /usr/local/lib/python3.7/site-packages/zou
WORKDIR ${ZOU_FOLDER}


COPY init_zou.sh /init_zou.sh
COPY upgrade_zou.sh /upgrade_zou.sh

# COPY scripts/init_zou.sh ./init_zou.sh
# COPY scripts/upgrade_zou.sh ./upgrade_zou.sh