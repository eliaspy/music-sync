# auth/tidal_auth.py
from flask import Blueprint, redirect, session, url_for, flash
import tidalapi
import os
import sys
import time
from dotenv import load_dotenv
load_dotenv()

tidal_bp = Blueprint('tidal_auth', __name__)

TIDAL_USERNAME = os.getenv("TIDAL_USERNAME")
TIDAL_PASSWORD = os.getenv("TIDAL_PASSWORD")

@tidal_bp.route('/login/tidal')
def login_tidal():
    global tidal_session
    try:
        tidal_session = tidalapi.Session()
        tidal_session.login_oauth_simple()
        # print(f"Tidal session: {dir(tidal_session)}")
        # tidal_session = [s for s in tidal_session if isinstance(s, tidalapi.Session)][0]
        session['tidal_session_id'] = tidal_session.session_id
        session['tidal_country_code'] = tidal_session.country_code
        session['tidal_user_id'] = tidal_session.user.id
        session['tidal_token'] = tidal_session.access_token
        session['tidal_refresh_token'] = tidal_session.refresh_token
        session['tidal_token_type'] = tidal_session.token_type
        session['tidal_expiry'] = tidal_session.expiry_time
        flash(f"✅ Tidal autenticado como {tidal_session.user.username}")
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        flash(f"❌ Error Tidal: {str(e)} Tipo: {exc_type}, Archivo: {fname}, Línea: {exc_tb.tb_lineno} ")
    return redirect('/')


def get_tidal_session():
    # Check if we have stored OAuth tokens in session
    if not all (k in session for k in ('tidal_token', 'tidal_refresh_token', 'tidal_token_type', 'tidal_expiry')):
        print("Tidal authentication required")
        redirect(url_for("tidal_auth.login_tidal", _external=True))

    tidal_session = tidalapi.Session()

    # Restore session from stored OAuth tokens
    tidal_session.load_oauth_session(
        access_token=session['tidal_token'],
        refresh_token=session['tidal_refresh_token'],
        token_type=session['tidal_token_type'],
        expiry_time=session['tidal_expiry']
    )

    return tidal_session