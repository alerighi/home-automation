#!/usr/bin/env python3

import json
import schedule

from paho.mqtt.client import Client, MQTTMessage


HOST = '192.168.1.200'
PORT = 1883
USERNAME = 'shelly'
PASSWORD = 'shelly'
CLIENT_ID = 'home-auto-python'

LIGHTS = {
    'camera': {
        'device': 'camera',
        'relay': '0',
        'version': 1,
    },
    'armadio': {
        'device': 'camera',
        'relay': '1',
        'version': 1,
    },
    'ufficio': {
        'device': 'ufficio',
        'relay': '0',
        'version': 1,
    },
    'scale': {
        'device': 'ufficio',
        'relay': '1',
        'version': 1,
    },
    'bagno': {
        'device': 'bagno',
        'relay': '0',
        'version': 2,
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

    def device_on_off(self, device, on: bool):
        if device['version'] == 1:
            self.client.publish(
                f"shellies/{device['device']}/relay/{device['relay']}/command", 'on' if on else 'off', qos=1)
        if device['version'] == 2:
            self.client.publish(f"shellies/{device['device']}/rpc", json.dumps(
                {"id": 123, "src": "user_1", "method": "Switch.Set", "params": {"id": device['relay'], "on": on}}), qos=1)

    def device_toggle(self, device):
        if device['version'] == 1:
            self.client.publish(
                f"shellies/{device['device']}/relay/{device['relay']}/command", 'toggle', qos=1)
        if device['version'] == 2:
            self.client.publish(f"shellies/{device['device']}/rpc", json.dumps(
                {"id": 123, "src": "user_1", "method": "Switch.Toggle", "params": {"id": device['relay']}}), qos=1)

    def all_off(self):
        for device in LIGHTS.values():
            self.device_on_off(device, False)

    def all_on(self):
        for device in LIGHTS.values():
            self.device_on_off(device, True)

    def start(self):
        self.client.connect(host=HOST, port=PORT, keepalive=60)
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


if __name__ == '__main__':
    HomeAutomation().start()
