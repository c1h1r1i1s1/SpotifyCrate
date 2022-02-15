import cred
import json
import requests
import base64
from urllib.parse import urlparse
import http.server

def main():

    global auth_code

    # Script for creating refresh token

    class LoginServer(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            global auth_code
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("<html><head><title>App Authorised Successfully</title></head>", "utf-8"))
            self.wfile.write(bytes("<body>", "utf-8"))
            self.wfile.write(bytes("<p>Thanks for authorising!</p>", "utf-8"))
            self.wfile.write(bytes("</body></html>", "utf-8"))
            query = urlparse(self.path).query
            auth_code = query.split("=")[1]
            print("\nAuth Code received")

    scope = "user-read-playback-state user-modify-playback-state"
    redirect_uri = "http://raspberrypi.local:8080/"
    auth_url = "https://accounts.spotify.com/authorize"
    token_url = 'https://accounts.spotify.com/api/token'
    auth_response = requests.get(auth_url, {
        'scope': scope,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'client_id': cred.client_id,
    })
    print("Copy and paste the following link into your browser:")
    print(auth_response.request.url)
    print()
    hostName = "0.0.0.0"
    serverPort = 8080
    webServer = http.server.HTTPServer((hostName, serverPort), LoginServer)
    print("Server started")
    try:
        while 1:
            webServer.handle_request()
            break
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped. Collecting Token...")

    encoded_client = "{}:{}".format(cred.client_id, cred.client_secret)
    encoded_client = encoded_client.encode('ascii')
    encoded_client = base64.b64encode(encoded_client)
    encoded_client = encoded_client.decode('ascii')
    headers = {
        'Authorization': 'Basic {}'.format(encoded_client),
        'Content-Type': "application/x-www-form-urlencoded"
    }
    auth_response = requests.post(token_url, {
        'redirect_uri': redirect_uri,
        'code': auth_code,
        'grant_type': "authorization_code",
    }, headers=headers)

    auth_response_data = auth_response.json()
    refresh_token = auth_response_data['refresh_token']
    creds = open("cred.py", 'r')
    old_creds = creds.readlines()
    old_creds.pop()
    old_creds.append("refresh_token='{}'".format(refresh_token))
    new_creds = old_creds
    creds.close()
    creds2 = open("cred.py", "w")
    creds2.writelines(new_creds)
    creds2.close()
    print("Access Token Received\n")

if __name__ == "__main__":
    main()
