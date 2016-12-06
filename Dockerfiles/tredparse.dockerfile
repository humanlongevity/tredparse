FROM continuumio/anaconda
MAINTAINER htang@humanlongevity.com

RUN apt-get update
RUN apt-get install -y gcc git build-essential
RUN apt-get install -y libncurses-dev libcurl4-openssl-dev zlib1g-dev
RUN pip install git+git://github.com/tanghaibao/tredparse.git
