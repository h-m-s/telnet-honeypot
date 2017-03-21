FROM ubuntu:14.04
RUN apt-get -y update \
    && apt-get -y install python3-pip \
    git \
    && pip3 install docker \
    && git clone -b refactor https://github.com/h-m-s/telnet-honeypot.git
CMD python3 /telnet-honeypot/telnet.py
