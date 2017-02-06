#!/usr/bin/env python3

from configparser import ConfigParser
import paho.mqtt.client as mqtt
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

# Read-in config
config = ConfigParser(delimiters=('=', ))
config.read('config.ini')

# Set safe maximum payload size
TOO_LONG = 2048


# MQTT connection callback
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT server with result code "+str(rc))


# Request Handler
class InternalRequestHandler(BaseHTTPRequestHandler):

    _mqtt_client = None

    def _deal_payload(self):
        payload = ''
        content_type = self.headers['content-type']
        if content_type != 'application/json':
            return (False, "Content-Type not JSON")

        remainbytes = int(self.headers['content-length'])
        line = self.rfile.read(remainbytes)
        remainbytes -= len(line)

        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)
        line = self.rfile.readline()
        remainbytes -= len(line)

        preline = self.rfile.readline()
        remainbytes -= len(preline)

        while remainbytes > 0:
            line = self.rfile.readline()
            remainbytes -= len(line)
            payload += line

        return payload

    def _exit_failure(self):
        self.send_response(400)  # Invalid
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes("Nope.", 'utf8'))
        return

    def do_GET(self):
        self.send_response(405)  # Method not allowed
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes("Please use POST.", 'utf8'))
        return

    def do_POST(self):
        content_len = int(self.headers['Content-Length'])

        if content_len < config['http'].getint('max_payload', 2048):
            payload = self.rfile.read(content_len)
        else:
            self._exit_failure()
            return

        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError:
            self._exit_failure()
            return

        if self._mqtt_client is not None:
            self._mqtt_client.publish(config['mqtt'].get('topic', 'default/topic'),
                                      json.dumps(data))

        self.send_response(200)  # OK
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes("Ok.", 'utf8'))
        return


# Main runner script
def run():

    # Setup MQTT client
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(config['mqtt'].get('hostname', '10.10.9.7'),
                   config['mqtt'].getint('port', 1883),
                   config['mqtt'].getint('timeout', 60))
    client.loop_start()

    InternalRequestHandler._mqtt_client = client

    # Setup HTTP server
    server_address = (config['http'].get('ip', ''),
                      config['http'].getint('port', 80))
    httpd = HTTPServer(server_address, InternalRequestHandler)
    print('Serving on ', server_address)
    httpd.serve_forever()

if __name__ == "__main__":
    run()
