from miniboa.async import TelnetServer, _on_connect, _on_disconnect, select
from engine.client import HoneyTelnetClient
from engine.cmd import run_cmd
import sys
import os

IDLE_TIMEOUT = 300


class HoneyTelnetServer(TelnetServer):
        def __init__(self, port=7777, address='', logger=None):
            """ Wrapper for the TelnetServer init """
            self.SERVER_RUN = 1
            self.logger = logger
            super().__init__(port, address, self.on_connect,
                             self.on_disconnect)
            self.client_list = []
            self.fake_files = []
            self.setup_fake_files()

        def setup_fake_files(self):
                for fake_file in os.listdir("./fakefiles/"):
                        self.fake_files += ["/{}".format(
                                fake_file.replace("%", "/"))]

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
                rlist, slist, elist = select.select(recv_list, send_list, [],
                                                    self.timeout)
            except select.error as err:
                # If we can't even use select(), game over man, game over
                logging.critical("SELECT socket error '{}'".format(str(err)))
                raise

            # Process socket file descriptors with data to recieve
            for sock_fileno in rlist:

                # If it's coming from the server's socket then this is a new
                #    connection request.
                if sock_fileno == self.server_fileno:

                    try:
                        sock, addr_tup = self.server_socket.accept()
                    except socket.error as err:
                        logging.error("ACCEPT socket error '{}:{}'.".format(
                                err[0], err[1]))
                        continue

                    # Check for maximum connections
                    if self.client_count() >= self.max_connections:
                        logging.warning("Refusing new connection, \
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
                    except ConnectionLost:
                        self.clients[sock_fileno].deactivate()

            # Process sockets with data to send
            for sock_fileno in slist:
                # Call the connection's send method
                self.clients[sock_fileno].socket_send()

        def clean_exit(self):
                """ cleans up any orphan containers on the way out """
                for client in self.client_list:
                        client.cleanup_container()
                        self.client_list.remove(client)
                self.SERVER_RUN = 0

        def on_connect(self, client):
                """
                On connect, logs the IP/port, appends
                the client to the client list, and
                sends the login message.
                """
                self.logger.info("Opened connection to {}".format(
                        client.addrport()))
                self.client_list.append(client)
                client.send("login: ")

        def on_disconnect(self, client):
                """
                for disconnections
                """
                self.logger.info("Lost connection to {}".format(
                        client.addrport()))
                client.cleanup_container()
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
                        if client.active and client.cmd_ready:
                                run_cmd(self, client)

        def login_screen(self, client, msg):
                """
                if we haven't got a user and a pass yet, force them to the
                login screen currently logs the user/pass but doesn't have
                any way of filtering them

                includes hacky workaround, sometimes control characters end up
                getting sent in with the username, so we'll just filter those
                here until we can figure out how to fix that?
                """
                if msg != "":
                        if not client.username:
                                if "#" in msg[0]:
                                        msg = msg[0].split("#")[1]
                                client.username = msg
                                client.send("password: ")
                        else:
                                client.password = msg[0]
                                self.return_prompt(client)
                                self.logger.info(
                                        "{} logged in as {}-{}".format(
                                                client.addrport(),
                                                client.username,
                                                client.password))

        def not_found(self, client, command):
                """
                not found
                """
                client.send("sh: {}: command not found\n".format(command))

        def return_prompt(self, client):
                """
                returns that prompt
                """
                prompt = "root@HMS:~# "
                client.send(prompt)
