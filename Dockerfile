FROM ubuntu:trusty
RUN apt-get -y update \
    && apt-get -y install python3-pip \
    wget \
    && pip3 install docker \
    && pip3 install miniboa \
    && wget https://raw.githubusercontent.com/h-m-s/telnet-honeypot/master/console.py
    && wget https://raw.githubusercontent.com/h-m-s/telnet-honeypot/master/mounts
CMD python3 ./console.py
