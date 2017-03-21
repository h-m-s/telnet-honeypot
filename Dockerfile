RUN apt-get -y update \
    && apt-get -y install python3-pip \
    git \
    && pip3 install docker \
    && git clone https://github.com/h-m-s/telnet-honeypot.git
CMD cd telnet-honeypot
CMD python3 ./console.py
