# Development Dockerfile to make testing easier under a standardized environment.
# XXX Do not use for production as-is

FROM python:2.7
LABEL maintainer Ginkgo Bioworks <devs@ginkgobioworks.com>

ARG DEBIAN_FRONTEND=noninteractive
ENV CURIOUS_HOME=/usr/src/curious
ENV SERVER_IP=0.0.0.0
ENV SERVER_PORT=8080

RUN apt-get update
RUN apt-get install --assume-yes apt-utils nodejs nodejs-legacy npm

RUN npm install --global bower

RUN mkdir -p $CURIOUS_HOME
WORKDIR $CURIOUS_HOME

COPY requirements.txt ./
RUN pip install --requirement requirements.txt

COPY . ./
RUN pip install --editable .
EXPOSE $SERVER_PORT
CMD ["make", "start"]
