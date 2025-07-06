from flask import Flask, redirect, request, session, url_for, render_template
import requests
import os
import base64
from urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify API credentials
SPOTIFY_CLIENT_ID = 'your_spotify_client_id'
SPOTIFY_CLIENT_SECRET = 'your_spotify_client_secret'
SPOTIFY_REDIRECT_URI = 'http://localhost:5000/callback'
SPOTIFY_AUTH_URL = 'https://accounts.spotify.com/authorize'
SPOTIFY_TOKEN_URL = 'https://accounts.spotify.com/api/token'
SPOTIFY_API_BASE_URL = 'https://api.spotify.com/v1'

SCOPE = 'playlist-read-private playlist-read-collaborative'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    auth_query = {
        'response_type': 'code',
        'redirect_uri': SPOTIFY_REDIRECT_URI,
        'scope': SCOPE,
        'client_id': SPOTIFY_CLIENT_ID
    }
    url_args = urlencode(auth_query)
    auth_url = f"{SPOTIFY_AUTH_URL}?{url_args}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')

    auth_str = f"{SPOTIFY_CLIENT_ID}:{SPOTIFY_CLIENT_SECRET}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()

    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI
    }

    token_headers = {
        'Authorization': f"Basic {b64_auth_str}"
    }

    r = requests.post(SPOTIFY_TOKEN_URL, data=token_data, headers=token_headers)
    token_response_data = r.json()

    session['access_token'] = token_response_data['access_token']

    return redirect(url_for('profile'))

@app.route('/profile')
def profile():
    access_token = session.get('access_token')
    if not access_token:
        return redirect(url_for('login'))

    headers = {
        'Authorization': f"Bearer {access_token}"
    }

    r = requests.get(f"{SPOTIFY_API_BASE_URL}/me/playlists", headers=headers)
    playlists = r.json()
    return render_template('profile.html', playlists=playlists)

if __name__ == '__main__':
    app.run(debug=True)

