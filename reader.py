import time
import cred
import json
import requests
import base64
from urllib.parse import urlparse
import http.server
import auth
import RPi.GPIO as GPIO
import pn532.pn532 as nfc
from pn532 import *

#Hat setup
pn532 = PN532_SPI(cs=4, reset=20, debug=False)
ic, ver, rev, support = pn532.get_firmware_version()
print('Found PN532 with firmware version: {0}.{1}'.format(ver, rev))
# Configure PN532 to communicate with NTAG215 cards
pn532.SAM_configuration()


if len(cred.refresh_token) < 1:
    print("Refresh token not found, running authorisation program...")
    auth.main()

class reader():

    def __init__(self):
        self.URI = "3HA1Ru1gEAgaxTywkJmBOL" # Backup congratulations

    def read(self):
        # go through blocks 6-11
        uri_bytes = []
        for i in range(6, 12):
            try:
                for x in pn532.ntag2xx_read_block(i):
                    uri_bytes.append(str(hex(x))[2:])
            except nfc.PN532Error as e:
                print(e.errmsg)
                break
        uri_bytes.pop()
        uri_bytes.pop()
        URI = [bytes.fromhex(elem).decode('utf-8') for elem in uri_bytes]
        self.URI = ''.join(URI)
        print("URI obtained: {}".format(self.URI))
        self.adder()

    def refresh(self):
        print("Refreshing Token...")
        token_url = 'https://accounts.spotify.com/api/token'
        encoded_client = "{}:{}".format(cred.client_id, cred.client_secret)
        encoded_client = encoded_client.encode('ascii')
        encoded_client = base64.b64encode(encoded_client)
        encoded_client = encoded_client.decode('ascii')
        self.refresh_token = cred.refresh_token
        headers = {
            'Authorization': 'Basic {}'.format(encoded_client),
            'Content-Type': "application/x-www-form-urlencoded"
        }
        auth_response = requests.post(token_url, {
            'refresh_token': self.refresh_token,
            'grant_type': "refresh_token",
        }, headers=headers)

        auth_response_data = auth_response.json()
        self.access_token = auth_response_data['access_token']
        print("Access Token Refreshed\n")

    def adder(self):
        print("Adding to que")
        
        dev_url = "https://api.spotify.com/v1/me/player/devices"
        try:
            headers = {
                'Authorization': 'Bearer {}'.format(self.access_token),
                'Content-Type': "application/json"
            }
        except AttributeError:
            self.refresh()
            headers = {
                'Authorization': 'Bearer {}'.format(self.access_token),
                'Content-Type': "application/json"
            }
        except:
            raise
        response = requests.get(dev_url, headers=headers)
        response = response.json()
        if "error" in response:
            if response["error"]["status"] == 401:
                self.refresh()
                headers = {
                    'Authorization': 'Bearer {}'.format(self.access_token),
                    'Content-Type': "application/json"
                }
                response = requests.get(dev_url, headers=headers)
                response = response.json()
        print("Getting device list...")
        active_found = False
        for device in response["devices"]:
            if device["name"] == "Spotify Crate":
                crate_found = True
                device_id = device["id"]
                print("Crate found!")
                break
            if device["is_active"]:
                active_found = True
                device_id = device["id"]
                print("Active device found, it's not the Crate")
        if not active_found and not crate_found:
            print("Warning: No active player nor Crate found. Adding to first")
            if len(response["devices"]) < 1:
                print("No players found! Please have spotify open on a device\n")
                return
            for device in response["devices"]:
                device_id = device["id"]
        print("Device selected\n")

        url = "https://api.spotify.com/v1/me/player/play?device_id={}".format(device_id)
        try:
            headers = {
                'Authorization': 'Bearer {}'.format(self.access_token),
                'Content-Type': "application/json"
            }
        except AttributeError:
            self.refresh()
            headers = {
                'Authorization': 'Bearer {}'.format(self.access_token),
                'Content-Type': "application/json"
            }
        except:
            raise
        json = {
            "context_uri": "spotify:album:{}".format(self.URI),
            "offset": {
                "position": 0
            },
            "position_ms": 0
        }
        response = requests.put(url=url, headers=headers, json=json)
        if not response.status_code in [204, 202]:
            if response.status_code == 401:
                self.refresh()
                headers = {
                    'Authorization': 'Bearer {}'.format(self.access_token),
                    'Content-Type': "application/json"
                }
                response = requests.get(url=url, headers=headers, json=json)
                response = response.json()
            else:
                print(response)

# Main loop:
master = reader()
UID_saved = []
print('Waiting for album card to read from!')
while True:
    try:
        # Check if a card is available to read
        uid = pn532.read_passive_target(timeout=1)
        # Try again if no card is available.
        if uid is not None:
            print('Found card with UID:', [hex(i) for i in uid])
            if UID_saved == [hex(i) for i in uid]:
                time.sleep(2)
            else:
                UID_saved = [hex(i) for i in uid]
                master.read()
    except KeyboardInterrupt:
        print("Stopping reader")
        GPIO.cleanup()
        quit()
    except:
        raise

GPIO.cleanup()
