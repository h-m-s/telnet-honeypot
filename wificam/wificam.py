#!/usr/bin/python3
"""
Research tool based on the following article:
https://pierrekim.github.io/blog/2017-03-08-camera-goahead-0day.html

Spins a really dead simple webserver that gives the proper GET and HEAD
responses for a GoAhead camera.

When the script from the article is ran, the server will give a response
with a planted username/pass appearing in the correct spot for the script
to grab it, and think it properly injected the ftp server with
the netcat listener.

This script alone does NOT currently start a netcat instance with the
attacker's server, but does grab the address of the server they're using
and the port they expect to see a netcat connection.

Next step is to implement this by starting a telnet client with a
HoneyTelnetServer with a special username/pass that puts the
HoneyTelnetServer in 'netcat mode', which should be basically
the same exact thing, without a prompt. May have to figure out
if we need to strip out any telnet control characters, etc? But
we can then connect this client directly to the netcat listener,
so for all intents and purposes, it should look exactly like the script
succeeded.

headers are set-up to appear as a GoAhead cam on Shodan:
https://www.shodan.io/search?query=GoAhead+5ccc069c403ebaf9f0171e9517f40e41

"""
import time
import subprocess
from subprocess import check_call
from http.server import BaseHTTPRequestHandler, HTTPServer

count = 0

server_address = ('0', 81)
"""
Set the address/port for your server here.
'0' will bind to all addresses. Port should be changed
here, as it will effect the header. Probably doesn't
matter if the header doesn't match the port, but
we're going for authenticity. ;)
"""

class GoAheadHandler(BaseHTTPRequestHandler):
  """
  Server to mimic a GoAhead camera web server, and appear on Shodan
  as a possible vulnerable camera, that returns the proper responses
  to the '0day' script to make attackers think they actually grabbed
  credentials or created a backdoor.
  """
  def date_time_string(self, timestamp=None):
    """
    Let's override the date_time_string function from the base
    so we look identical to a GoAhead cam on Shodan. Nitpicky detail,
    but let's not confuse any bots!
    """
    if timestamp is None:
      timestamp = time.time()
      year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
      s = "%s %3s %0d %02d:%02d:%02d %4d" % (
        self.weekdayname[wd],
        self.monthname[month], day,
        hh, mm, ss, year)
      return s


  def do_HEAD(self):
    """
    Just causes a HEAD request call up the default do_GET message.
    """
    self.do_GET()

  def netcat_honeypot(self, ahost, aport):
    """
    Designed to work with the H-M-S telnet honeypot.
    Starts up netcat and logs in with the net/cat user,
    which mainly just drops the prompt so it looks more like
    an actual instance of sh running over netcat. :)

    Not super sure this is the ideal method to do this, but it
    works for the minute!
    """

    subprocess.Popen("./snetcet.sh")

#    fifo = open("./pipe", "w+")
#tail -f pipe | nc 138.68.229.32 1337 | tee outgoing.log | nc 127.0.0.1 23 | tee pipe
#    tail = subprocess.Popen("tail -f pipe".split(" "), stdout=subprocess.PIPE)
#    nc1 = subprocess.Popen("nc {} {}".format(ahost, aport).split(" "), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#    tee1 = subprocess.Popen("tee outgoing.log".split(" "), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#    nc2 = subprocess.Popen("nc 127.0.0.1 23".split(" "), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
#    tee2 = subprocess.Popen("tee pipe".split(" "), stdin=subprocess.PIPE)

  def do_GET(self):
    """
    Handles all GET requests, including the attacks.
    """
    global count
    self.server_version = "GoAhead-Webs"
    self.sys_version = ""
    msg = "Hello world!"
    print("Got a GET request.")
    if "/system.ini?loginuse&loginpas" in self.requestline:
      """
      This is the line the script uses to snag credentials.
      Currently this just fills in the execess space with 'b's.
      It'd be pretty obvious if you were dumping the output of the script,
      but if you just compile the 0-day script as given and
      run it against this server, it prints to the screen:

      [+] bypassing auth ... done
          login = minad
          pass  = damin
      [+] planting payload ... done
      [+] executing payload ... done
      [+] cleaning payload ... done
      [+] cleaning payload ... done
      [+] enjoy your root shell on REMOTE_HOST:REMOTE_PORT

      It only checks to see that it can harvest the login/pass from the
      step that grabs credentials, and never checks the response from
      the payload itself.
      """
      print("Attacker attempting to get credentials! Sending fake creds...")
      count = 1
      msg = ("b" * 137) #filler, attack script will skip this to look for uname
      msg += "minad" #username
      msg += ("\0" * 27) # more filler, script skips forward 27 for pass
      msg += "damin" #password
      self.send_response(200)
      self.send_header('Content-type','text/html')
      self.end_headers()
      self.wfile.write(bytes.fromhex('0a0a0a0a01') + bytes(msg, "utf8"))
    elif count > 0:
      """
      The first payload the script sends
      contains the login/pass (which should match the ones you provided
      above), but more importantly it contains the server
      and port the attacker should have a netcat listener open on.

      You'd need to connect to this port to make the attacker think they have
      full access.
      """
      for line in self.requestline.split("&"):
        if "loginuse" in line:
          print("Attacker using login: {}".format(line.split("=")[1]))
        if "loginpas" in line:
          print("Attacker using password: {}".format(line.split("=")[1]))
        if "pwd" in line:
          temp = line.split("%20")[1].split("+")
          print("Attacker remote server: {} port: {}".format(temp[0], temp[1]))
          self.netcat_honeypot(temp[0], temp[1])
      count -= 1
    else:
      """
      This basically just covers any old GET or HEAD request.
      Fills in the proper headers for a GoAhead camera and the default 401.
      Would be nice to actually have some sort of landing page for the correct
      user/password, because it's going to make the attacker think they obtained
      credentials.

      Perhaps just log every username/pass entered, and set the credentials
      harvested from the script to something unique, so we'd know who
      successfully launched the script, and never have anything past this
      portal.
      """
      msg = "<html><head><title>Document Error: Unauthorized</title></head>\n"
      msg += "                <body><h2>Access Error: Unauthorized</h2>\n"
      msg += "                <p>Access to this document requires a User ID</p></body></html>\n\n"
      self.send_response(401)
      self.send_header('WWW-Authenticate', 'Digest realm="GoAhead", domain=":{}",qop="auth", nonce="a32f2b51bcb55c24d003a21be5ec0345", opaque="5ccc069c403ebaf9f0171e9517f40e41",algorithm="MD5", stale="FALSE"'.format(server_address[1]))
      self.send_header('Pragma', 'no-cache')
      self.send_header('Cache-Control', 'no-cache')
      self.send_header('Content-type','text/html')
      self.end_headers()
      self.wfile.write(bytes(msg, "utf8"))
    return

def run():
  """
  Loop to start the server up, bound to all addresses, on the given port.
  If you change the port, it should change the headers to reflect your new port.
  """
  print('starting server...')
  httpd = HTTPServer(server_address, GoAheadHandler)
  print('running server...')
  httpd.serve_forever()

run()
