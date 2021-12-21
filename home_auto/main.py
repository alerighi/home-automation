#!/usr/bin/env python3

import json
import schedule
import random
import threading
import urllib.parse

from http.server import HTTPServer, BaseHTTPRequestHandler
from paho.mqtt.client import Client, MQTTMessage

WEB_HOST = '0.0.0.0'
WEB_PORT = 8080
MQTT_HOST = '127.0.0.1'
MQTT_PORT = 1883
USERNAME = 'shelly'
PASSWORD = 'shelly'
CLIENT_ID = 'home-auto-python-' + random.randbytes(6).hex()

LIGHTS = {
    'camera': {
        'device': 'camera',
        'relay': '0',
        'version': 1,
        'state': -1,
    },
    'armadio': {
        'device': 'camera',
        'relay': '1',
        'version': 1,
        'state': -1,
    },
    'ufficio': {
        'device': 'ufficio',
        'relay': '0',
        'version': 1,
        'state': -1,
    },
    'scale': {
        'device': 'ufficio',
        'relay': '1',
        'version': 1,
        'state': -1,
    },
    'bagno': {
        'device': 'bagno',
        'relay': '0',
        'version': 2,
        'state': -1,
    }
}


class HomeAutomation:
    def __init__(self):
        self.client = Client(client_id=CLIENT_ID)
        self.client.username_pw_set(username=USERNAME, password=PASSWORD)

        self.last_button_1_state = False
        self.last_button_2_state = False

    def on_mqtt_message(self, client: Client, userdata, msg: MQTTMessage):
        print(msg.topic + " " + str(msg.payload))
        if msg.topic == 'shellies/i3/input/0' and msg.payload == b'1' and (self.last_button_1_state == False):
            self.last_button_1_state = True
            self.all_on()
        if msg.topic == 'shellies/i3/input/0' and msg.payload == b'0' and self.last_button_1_state == True:
            self.last_button_1_state = False
            self.all_off()
        if msg.topic == 'shellies/i3/input/1' and int(msg.payload) != self.last_button_2_state:
            self.last_button_2_state = int(msg.payload)
            self.device_toggle(LIGHTS['ufficio'])

        # collect state from MQTT to align to physical switch action
        if msg.topic == 'shellies/ufficio/relay/0':
            LIGHTS['ufficio']['state'] = int(msg.payload == b'on')
        if msg.topic == 'shellies/ufficio/relay/1':
            LIGHTS['scale']['state'] = int(msg.payload == b'on')
        if msg.topic == 'shellies/camera/relay/0':
            LIGHTS['camera']['state'] = int(msg.payload == b'on')
        if msg.topic == 'shellies/camera/relay/1':
            LIGHTS['armadio']['state'] = int(msg.payload == b'on')
        if msg.topic == 'shellies/bagno/status/switch:0':
            LIGHTS['bagno']['state'] = int(json.loads(msg.payload)['output'])

    def device_on_off(self, device, on: bool):
        if device['version'] == 1:
            self.client.publish(
                f"shellies/{device['device']}/relay/{device['relay']}/command", 'on' if on else 'off', qos=1)
        if device['version'] == 2:
            self.client.publish(f"shellies/{device['device']}/rpc", json.dumps(
                {"id": 123, "src": "user_1", "method": "Switch.Set", "params": {"id": device['relay'], "on": on}}), qos=1)
        device['state'] = int(on)

    def device_toggle(self, device):
        if device['version'] == 1:
            self.client.publish(
                f"shellies/{device['device']}/relay/{device['relay']}/command", 'toggle', qos=1)
        if device['version'] == 2:
            self.client.publish(f"shellies/{device['device']}/rpc", json.dumps(
                {"id": 123, "src": "user_1", "method": "Switch.Toggle", "params": {"id": device['relay']}}), qos=1)
        device['state'] = int(not device['state'])

    def all_off(self):
        for device in LIGHTS.values():
            self.device_on_off(device, False)
            device['state'] = 0

    def all_on(self):
        for device in LIGHTS.values():
            self.device_on_off(device, True)
            device['state'] = 1

    def start(self):
        self.client.connect(host=MQTT_HOST, port=MQTT_PORT, keepalive=60)
        self.client.subscribe('#')
        self.client.publish('home-auto/events',
                            json.dumps({'event': 'started'}))
        self.client.on_message = lambda client, userdata, msg: self.on_mqtt_message(
            client, userdata, msg)

        # turn every light off at 9am when I go out to work
        schedule.every().day.at("09:00").do(lambda: self.all_off())

        while True:
            self.client.loop()
            schedule.run_pending()


home_automation = HomeAutomation()


class HomeAutomationHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        args = urllib.parse.parse_qs(url.query)

        if url.path == '/light':
            if 'on' in args and 'light' in args:
                light = args['light'][0]
                on = args['on'][0]

                if on == 'true' or on == '1':
                    home_automation.device_on_off(LIGHTS[light], True)
                elif on == 'false' or on == '0':
                    home_automation.device_on_off(LIGHTS[light], False)
                elif on == 'toggle':
                    home_automation.device_toggle(LIGHTS[light])

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(LIGHTS).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()


def main():
    threading.Thread(target=lambda: home_automation.start()).start()
    HTTPServer((WEB_HOST, WEB_PORT), HomeAutomationHandler).serve_forever()


if __name__ == '__main__':
    main()
