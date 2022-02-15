import cred
import json
import requests
import base64
from urllib.parse import urlparse
import http.server
import auth

if len(cred.refresh_token) < 1:
    print("Refresh token not found, running authorisation program...")
    auth.main()

class reader():

    def __init__(self):
        self.URI = "3HA1Ru1gEAgaxTywkJmBOL" # Backup congratulations

    def read(self):
        # Use NFC Reader to get URI
        self.URI = "3HA1Ru1gEAgaxTywkJmBOL" # Congratulations

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
            if device["is_active"]:
                active_found = True
                device_id = device["id"]
                print("Active device found")
                break
        if not active_found:
            print("Warning: No active player found. Adding to first")
            if len(response["devices"]) < 1:
                print("No players found! Returning...\n")
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
        if not response.status_code == 204:
            response = response.json()
            if "error" in response:
                if response["error"]["status"] == 401:
                    self.refresh()
                    headers = {
                        'Authorization': 'Bearer {}'.format(self.access_token),
                        'Content-Type': "application/json"
                    }
                    response = requests.get(url=url, headers=headers, json=json)
                    response = response.json()
                else:
                    print(response)

master = reader()
master.read()
master.adder()
