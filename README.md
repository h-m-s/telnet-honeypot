# Honeypot Management System
### AKA Her Majesty's Ship

*Created by [HoldenGs](https://github.com/HoldenGs/) and [Wintermanc3r](https://github.com/wintermanc3r/)*

Honeypot Management System is the term we have created for the use of honeypots as docker images on Docker machines in Swarm Mode. Knowledge of Swarm Mode is required to fully utilize this server as a fully-fledged honeypot management system, though you can still run this image alone.


#### So far we have a single honeypot image designed to run on the swarm. We will be creating more images and adding them here.

We want to build out more features; here is a list of what we've done and our planned features:

*Bold Text == Finished feature*
* **Example Honeypot, used in Hackathon**
* More honeypots
* Swarm Manager Honeypot Scaling Automation
* Automated Port Forwarding
* Swarm Mode startup guide

The telnet-honeypot image runs a telnet server with a python console mediating client access while emulating an insecure server on a docker container. Downloaded binaries get redirected to the logs folder.



Run like so:
~~~~
docker run -itd -v /var/run/docker.sock:/var/run/docker.sock -p 23:23 telnet_honeypot
~~~~

The -v option ensures the host docker daemon is mounted as a volume to the container.

The -p option publishes the port the telnet server needs to communicate through.

To run as a service in a swarm, you'll need to use the following syntax:
~~~~
docker service create --mode replicated --publish mode=host,target=7777,published=7777 \
       --mount type=bind,source=/var/run/docker.sock,target=/var/run/docker.sock \
       --name run-honeypot holdengs/telnet-honeypot
~~~~
