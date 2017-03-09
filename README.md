# Honeypot Management System
## (AKA Her Majesty's Ship)

Created by [HoldenGs](https://github.com/HoldenGs/) and [Wintermanc3r](https://github.com/wintermanc3r/)

The telnet-honeypot image runs a telnet server with a python console mediating client access while emulating an insecure server on a docker container. Downloaded binaries get redirected to the logs folder.

This image requires docker to be installed on its host. This should not be run on your local machine.

Run like so:
~~~~
docker run -v /var/run/docker.sock:/var/run/docker.sock -p 7777:7777 telnet-honeypot
~~~~

The -v option ensures the host docker daemon is mounted as a volume to the container.

The -p option publishes the port the telnet server needs to communicate through.

To run as a service in a swarm, you'll need to use the following syntax:
~~~~
docker service create --mode replicated --publish mode=host,target=7777,published=7777 \
       --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
       --name run-honeypot holdengs/telnet-honeypot
~~~~
