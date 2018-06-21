#!/usr/bin/python
import BaseHTTPServer

ip='127.0.0.1'
port=54321

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(s):
        """Respond to a GET request."""
        s.send_response(200)
        s.send_header("Content-type", "text/html")
        s.end_headers()

server_address = (ip, port)
httpd = BaseHTTPServer.HTTPServer(server_address, MyHandler)
httpd.handle_request()
