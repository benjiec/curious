FROM python:2.7

RUN apt-get update
RUN apt-get install -y npm
RUN apt-get install -y nodejs
RUN ln -s /usr/bin/nodejs /usr/bin/node

RUN npm install -g bower

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ENV CURIOUS_HOME /curious
RUN mkdir -p $CURIOUS_HOME
COPY . $CURIOUS_HOME
WORKDIR $CURIOUS_HOME

RUN bower install --allow-root
