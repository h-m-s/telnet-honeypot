FROM ubuntu:trusty
RUN apt-get -y update
RUN apt-get -y install python3-pip \
    	       	       git
RUN pip3 install docker
RUN git clone https://github.com/H-M-S/honeypot_management_system
CMD python3 /honeypot_management_system/console.py
