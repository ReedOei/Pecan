FROM ubuntu:18.04

# Setup basic environment
RUN apt-get update
RUN apt-get install -y software-properties-common

# Install git
RUN apt-get install -y git
RUN git --version

# Install python
RUN apt-get update
RUN apt-get install -y python3 python3-dev python3-pip
RUN pip3 install pytest
RUN rm -rf /var/lib/apt/lists/*

ENV PYTHONIOENCODING utf-8

# Install misc
RUN apt-get update
RUN apt-get install -y sudo vim wget curl

# Install spot. Run this here so that if we make changes to the stuff below, we don't have to rebuild spot
RUN curl -sSL https://raw.githubusercontent.com/ReedOei/Pecan/master/scripts/install-spot.sh | bash

WORKDIR /home/pecan

RUN git clone "https://github.com/ReedOei/Pecan" "ReedOei/Pecan"

WORKDIR /home/pecan/ReedOei/Pecan

RUN git pull
RUN pip3 install -r requirements.txt
# Install my custom version of PySimpleAutomata
RUN ( cd PySimpleAutomata; pip3 install . )
RUN pytest --verbose test

