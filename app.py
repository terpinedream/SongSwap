from flask import Flask, redirect, request, session, url_for, render_template
import requests
from dotenv import load_dotenv
import os
import base64
from urllib.parse import urlencode

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_secret_key')

# Spotify API credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')
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
    if not code:
        return "No code provided by Spotify.", 400

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

    access_token = token_response_data.get('access_token')
    if not access_token:
        return f"Error getting access token: {token_response_data}", 400

    session['access_token'] = access_token
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
    return render_template('profile.html', playlists=playlists.get ("items", []))

def get_playlist_tracks(access_token, playlist_id):
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    tracks = []
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    
    while url:
        r = requests.get(url, headers=headers)
        data = r.json()
        for item in data['items']:
            track = item['track']
            # Some tracks can be None or unavailable, skip them
            if track:
                tracks.append(track)
        url = data.get('next')  # Spotify paginates, get next page URL
    
    return tracks

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

