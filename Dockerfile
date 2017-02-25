FROM ubuntu:trusty
RUN apt-get -y update && apt-get install apt-utils && apt-get -y install docker && apt-get -y install docker.io && apt-get -y install python3-pip && pip3 install docker && apt-get -y install git && git clone https://github.com/HoldenGs/honeypot_management_system
CMD python3 /honeypot_management_system/console.py
