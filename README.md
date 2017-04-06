# Honeypot Management System
### AKA Her Majesty's Ship

*Created by [HoldenGs](https://github.com/HoldenGs/) and [Wintermanc3r](https://github.com/wintermanc3r/)*


This repo is designed to function as a Telnet honeypot. A Telnet connection is established with connecting clients,
and the input is parsed in Python before either sending a scripted response or a resposne made through
a Docker container.


A brief overview:

  Asynchronous (Mini-Boa) server starts up, and loops through checking for clients and checking client input.

  Client connects, and a handler is created for the client, and a new Docker container is spun up for the client.
  Telnet negotation takes place and client is presented with login screen.
  Client's input is parsed through engine/cmd, which has a loop for parsing out logical operators.
  Command execution is threaded, to keep a client's command from hanging up the entire server.
  	   Depending on the command, scripted input may be sent back, or the command will be ran through
	   the client's Docker container. This allows us to decide which commands we run, and which commands
	   we'd rather not run directly in the container, allowing us to spoof things like /proc/mounts and
	   headers from /bin/echo.
  Response is sent back to the client.
  The difference is checked between the client's container and the base container after every command.
  If there's a new or changed file and we don't already have a copy, it'll be TAR'd and saved in logs/
  Checking after every command is a little extreme, but it ensures altered files can't be removed before we
  snag a copy.

  When a client disconnects, his handler is set as inactive and will be removed on the main server's loop.
  On disconnect, the Docker container is checked one last time for changes and spun down.



Installation:
~~~~

Ensure you're running the latest version of Docker. Docker provides an easy install script that you can use:
`-sSL https://get.docker.com/ | sh` after removing any old versions of Docker or docker.io

This image can be built with `docker build -t telnet_honeypot .`

and will also require you to build the image in images/ as whatever name you have set in the
configuration file. Default tag is honeybox.

Run like so:
~~~~
docker run -itd -v /var/run/docker.sock:/var/run/docker.sock -p 23:23 telnet_honeypot
~~~~

The -v option ensures the host docker socket is mounted as a volume to the container.

Full disclosure: The security of this has been questioned! Please be aware of the
consequences of mounting the socket as such, and be sure to never run this
on a host system that may contain personal or sensitive information.
It is, in my opinion, highly unlikely that an attacker could escape from the
container, but precautions should always be taken!

The -p option publishes the port the telnet server needs to communicate through.