import threading
from miniboa.async import TelnetServer, _on_connect, _on_disconnect, select
from engine.client import HoneyTelnetClient
from engine.cmd import run_cmd
from patterns.patterns import check_list
from engine.threads import CommandThread
import threading
import sys
import os
import re
import time

IDLE_TIMEOUT = 120

class HoneyTelnetServer(TelnetServer):
        def __init__(self, port=7777, address='', logger=None):
                """ Wrapper for the TelnetServer init """
                self.SERVER_RUN = True
                self.logger = logger
                super().__init__(port, address, self.on_connect,
                                 self.on_disconnect)
                self.client_list = []
                self.threadlock = threading.Lock()
                self.threads = {}
                self.prompt = "/ # "
                self.username = None
                self.password = None

        def poll(self):
            """
            Taken from the miniboa source, modified to call up the wrapper
            so we can extend out the client a little bit.

            From miniboa:
            Perform a non-blocking scan of recv and send states on the server
            and client connection sockets.  Process new connection requests,
            read incomming data, and send outgoing data.  Sends and receives
            may be partial.
            """
            # Build a list of connections to test for receive data pending
            recv_list = [self.server_fileno]    # always add the server
            del_list = []    # list of clients to delete after polling
            for client in self.clients.values():
                if client.active:
                    recv_list.append(client.fileno)
                else:
                    self.on_disconnect(client)
                    del_list.append(client.fileno)
            # Delete inactive connections from the dictionary
            for client in del_list:
                del self.clients[client]

            # Build a list of connections that need to send data
            send_list = []
            for client in self.clients.values():
                if client.send_pending:
                    send_list.append(client.fileno)

            # Get active socket file descriptors from select.select()
            try:
                rlist, slist, elist = select.select(
                        recv_list, send_list, [], self.timeout)
            except InterruptedError as err:
                    return
            except select.error as err:
                # If we can't even use select(), game over man, game over
                self.logger.critical(
                        "SELECT socket error '{}'".format(str(err)))
                raise

            # Process socket file descriptors with data to recieve
            for sock_fileno in rlist:

                # If it's coming from the server's socket then this is a new
                #    connection request.
                if sock_fileno == self.server_fileno:

                    try:
                        sock, addr_tup = self.server_socket.accept()
                    except Exception as err:
                        self.logger.error("ACCEPT socket error")
                        continue

                    # Check for maximum connections
                    if self.client_count() >= self.max_connections:
                        self.logger.warning("Refusing new connection, \
                                         maximum already in use.")
                        sock.close()
                        continue

                    # Create the client instance
                    new_client = HoneyTelnetClient(sock, addr_tup)

                    # Add the connection to our dictionary and call handler
                    self.clients[new_client.fileno] = new_client
                    self.on_connect(new_client)

                else:
                    # Call the connection's recieve method
                    try:
                        self.clients[sock_fileno].socket_recv()
                    except:
                        self.clients[sock_fileno].deactivate()

            # Process sockets with data to send
            for sock_fileno in slist:
                # Call the connection's send method
                self.clients[sock_fileno].socket_send()

        def clean_exit(self):
                """ cleans up any orphan containers on the way out """
                for client in self.client_list:
                        client.cleanup_container(self)
                        client.active = 0
                self.SERVER_RUN = False

        def on_connect(self, client):
                """
                On connect, logs the IP/port, appends
                the client to the client list, and
                sends the login message.
                """
                self.logger.info("Opened connection to {}".format(
                        client.addrport()))
                self.client_list.append(client)
                if client.addrport().split(":")[0] == "127.0.0.1":
                        client.mode = "netcat"
                        client.username = "netcat"
                        client.password = "local"
                else:
                        client.mode = "telnet"
                        client.request_terminal_type()
                        client.send("login: ")

        def on_disconnect(self, client):
                """
                for disconnections
                """
                self.logger.info("Lost connection to {}".format(
                        client.addrport()))
                client.cleanup_container(self)
                check_list(client, self)
                self.client_list.remove(client)

        def kick_idle(self):
                """
                kicks idle client
                """
                for client in self.client_list:
                        if client.idle() > IDLE_TIMEOUT:
                                self.logger.info("Kicking idle client from {}".
                                                 format(client.addrport()))
                                client.active = False

        def process_clients(self):
                """
                if client has a cmd ready, let's run it
                """
                for client in self.client_list:
                        if (client.active and
                            client.cmd_ready):
                                command = re.sub(r'(\x00)$', '', client.get_command())
                                self.threadlock.acquire()
                                if (client.ip not in self.threads or
                                    self.threads[str(client.ip)] is None):
                                        self.logger.debug(
                                                "Spawning up a new thread.")
                                        client.active_cmds += [
                                                command]
                                        self.threadlock.release()
                                        self.threads[client.ip] = CommandThread(
                                                client, self, name="thread")
                                        self.threads[client.ip].start()
                                else:
                                        self.logger.debug(
                                                "Running in existing thread.")
                                        client.active_cmds += [
                                            command]
                                        self.threadlock.release()


        def login_screen(self, client, msg):
                """
                if we haven't got a user and a pass yet, force them to the
                login screen currently logs the user/pass but doesn't have
                any way of filtering them

                includes hacky workaround, sometimes control characters end up
                getting sent in with the username, so we'll just filter those
                here until we can figure out how to fix that?
                """
                if msg != "" and client.mode == "telnet":
                        if not client.username:
                                if "#" in msg[0]:
                                        msg = msg[0].split("#")[1]
                                client.username = msg[0]
                                client.send("Password: ")
                        else:
                                client.password = msg[0]
                                if (self.username is not None and
                                    self.username != client.username or
                                    self.password != client.password):
                                        client.send("Login incorrect\n\n")
                                        client.username = None
                                        client.password = None
                                        client.send("login: ")
                                        return
                                self.return_prompt(client)
                                self.logger.info(
                                        "{} logged in as {}-{}".format(
                                                client.addrport(),
                                                client.username,
                                                client.password))

        def return_prompt(self, client):
                """
                returns that prompt
                """
                if client.mode == "telnet" and client.passwd_flag is None:
                        client.send(self.prompt)
