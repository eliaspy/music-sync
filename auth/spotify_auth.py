# auth/spotify_auth.py
from flask import Blueprint, redirect, session, request, url_for, flash
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import time
load_dotenv()
spotify_bp = Blueprint('spotify_auth', __name__)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SP_OAUTH = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope="user-library-read playlist-read-private"
    )

@spotify_bp.route('/login/spotify')
def login_spotify():
    return redirect(SP_OAUTH.get_authorize_url())

@spotify_bp.route('/callback/spotify')
def callback_spotify():
    code = SP_OAUTH.parse_response_code(url_for('spotify_auth.callback_spotify', _external=True) + '?' + request.query_string.decode())
    token_info = SP_OAUTH.get_access_token(code)
    session['spotify_token_info'] = token_info
    return redirect(url_for('index'))

def get_spotify_client():
    token_info = SP_OAUTH.get_cached_token()

    if not token_info:
        print("No cached token found, user must log in")
        raise Exception("Spotify authentication required")

    if token_info['expires_at'] - int(time.time()) < 60:
        print("Token expired, refreshing...")
        token_info = SP_OAUTH.refresh_access_token(token_info['refresh_token'])
        print("DEBUG refreshed token_info:", token_info)

    sp = spotipy.Spotify(auth=token_info['access_token'])
    print("DEBUG spotipy client created:", sp)
    return sp