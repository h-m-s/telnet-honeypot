
#!/usr/bin/env python
"""
attempt to emulate the following article:
https://pierrekim.github.io/blog/2017-03-08-camera-goahead-0day.html

headers set-up to appear as a GoAhead cam on Shodan:
https://www.shodan.io/search?query=GoAhead+5ccc069c403ebaf9f0171e9517f40e41

TODO:
***
connect to the netcat listener! we already parse out
where we're supposed to connect to..

i think we could essentially write a telnet client,
connect to the honey server, and pipe it all through netcat
so it looks like it's a direct line to /bin/sh

just open the client, give a special user pass that
starts the server in 'netcat mode' where
there's no prompt, and pass control to netcat :)

server could look for user: net password: cat
and set a flag on the client obj that
determines if we're in telnet or netcat mode.
***

***
change headers so we appear the same as a GoAhead cam on shodan !!!!
***

"""
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

global count
count = 0

class testHTTPServer_RequestHandler(BaseHTTPRequestHandler):
  def date_time_string(self, timestamp=None):
    """ Let's override the date_time_string function from the base
    so we look identical to a GoAhead cam on Shodan. Nitpicky detail,
    but let's not confuse any bots!"""
    if timestamp is None:
      timestamp = time.time()
      year, month, day, hh, mm, ss, wd, y, z = time.gmtime(timestamp)
      s = "%s %3s %0d %02d:%02d:%02d %4d" % (
        self.weekdayname[wd],
        self.monthname[month], day,
        hh, mm, ss, year)
      return s


  def do_HEAD(self):
    self.do_GET()

  def do_GET(self):
    self.server_version = "GoAhead-Webs"
    self.sys_version = ""
    global count
    msg = "Hello world!"
    print("Got a GET request.")
    if "/system.ini?loginuse&loginpas" in self.requestline:
      print("Attacker attempting to get credentials! Sending fake creds...")
      count = 1
      msg = ("a" * 137) #filler, attack script will skip this to look for uname
      msg += "admin" #username
      msg += ("\0" * 27) # more filler, script skips forward 27 for pass
      msg += "admin" #password
      self.send_response(200)
      self.send_header('Content-type','text/html')
      self.end_headers()
      self.wfile.write(bytes.fromhex('0a0a0a0a01') + bytes(msg, "utf8"))
    elif count > 0:
      for line in self.requestline.split("&"):
        if "loginuse" in line:
          print("Attacker using login: {}".format(line.split("=")[1]))
        if "loginpas" in line:
          print("Attacker using password: {}".format(line.split("=")[1]))
        if "pwd" in line:
          temp = line.split("%20")[1].split("+")
          print("Attacker remote server: {} port: {}".format(temp[0], temp[1]))
      count -= 1
    else:
      msg = "<html><head><title>Document Error: Unauthorized</title></head>\n"
      msg += "                <body><h2>Access Error: Unauthorized</h2>\n"
      msg += "                <p>Access to this document requires a User ID</p></body></html>\n\n"
      self.send_response(401)
      self.send_header('WWW-Authenticate', 'Digest realm="GoAhead", domain=":81",qop="auth", nonce="a32f2b51bcb55c24d003a21be5ec0345", opaque="5ccc069c403ebaf9f0171e9517f40e41",algorithm="MD5", stale="FALSE"')
      self.send_header('Pragma', 'no-cache')
      self.send_header('Cache-Control', 'no-cache')
      self.send_header('Content-type','text/html')
      self.end_headers()
      self.wfile.write(bytes(msg, "utf8"))
    return

def run():
  global count
  count = 0
  print('starting server...')
  server_address = ('0', 81)
  httpd = HTTPServer(server_address, testHTTPServer_RequestHandler)
  print('running server...')
  httpd.serve_forever()

run()
