FROM ubuntu:trusty
RUN apt-get -y update \
    && apt-get -y install python3-pip \
    wget \
    && pip3 install docker \
    && pip3 install miniboa \
    && wget https://raw.githubusercontent.com/h-m-s/telnet-honeypot/master/console.py
CMD python3 ./console.py
