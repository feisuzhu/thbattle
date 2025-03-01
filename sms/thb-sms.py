# -*- coding: utf-8 -*-

# -- stdlib --
from pathlib import Path
import argparse
import logging
import time

# -- third party --
import requests
import dbus

# -- own --

# -- code --
class SMSAgent:
    def __init__(self, callback_url):
        self.callback_url = callback_url
        self.subscriber = None

        # Connect to system bus
        self.bus = dbus.SystemBus()

        # Get ModemManager interface
        self.modem = self.bus.get_object(
            'org.freedesktop.ModemManager1',
            '/org/freedesktop/ModemManager1/Modem/0',
        )
        self.messages = dbus.Interface(
            self.modem,
            'org.freedesktop.ModemManager1.Modem.Messaging',
        )
        subscriber = str(self.modem.Get(
            'org.freedesktop.ModemManager1.Modem', 'OwnNumbers',
            dbus_interface='org.freedesktop.DBus.Properties',
        ))

        if subscriber.startswith('+86'):
            subscriber = subscriber[3:]
        elif subscriber.startswith('86'):
            subscriber = subscriber[2:]

        self.subscriber = subscriber

    def handle_sms(self, sender, text, timestamp):
        if sender.startswith('+86'):
            sender = sender[3:]

        ts = time.strftime('%y%m%d %H:%M:%S')
        print(f"\033[32m[{ts}]\033[0m Processing SMS from {sender}: {text}")

        payload = {
            'time': timestamp,
            'sender': sender,
            'receiver': self.subscriber,
            'text': text
        }

        resp = requests.post(
            self.callback_url,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        resp.raise_for_status()

    def run(self):
        messaging = self.messages

        while True:
            try:
                messages = messaging.List()
                for msg_path in messages:
                    print('got message', msg_path)
                    msg = self.bus.get_object('org.freedesktop.ModemManager1', msg_path)
                    msg_props = msg.GetAll('org.freedesktop.ModemManager1.Sms',
                                         dbus_interface='org.freedesktop.DBus.Properties')

                    # Process message
                    self.handle_sms(
                        str(msg_props.get('Number', '')),
                        str(msg_props.get('Text', '')),
                        str(msg_props.get('Timestamp', 0)),
                    )

                    for _ in range(10):
                        try:
                            messaging.Delete(msg_path)
                            break
                        except Exception:
                            time.sleep(1)

                time.sleep(1)

            except Exception as e:
                import traceback
                traceback.print_exc()
                time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--callback', default='http://proton:feisuzhu@192.168.233.11:8000/.callbacks/sms-verification',
                       help='Callback URL for received messages')
    args = parser.parse_args()

    agent = SMSAgent(args.callback)
    agent.run()
