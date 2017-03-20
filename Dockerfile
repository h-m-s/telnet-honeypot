FROM ubuntu:trusty
RUN apt-get -y update \
    && apt-get -y install python3-pip \
    git \
    && pip3 install docker \
    && git clone https://github.com/h-m-s/honeypot_management_system
CMD python3 /honeypot_management_system/console.py
