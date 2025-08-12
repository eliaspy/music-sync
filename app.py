from werkzeug.utils import secure_filename
from flask import Flask, render_template, redirect,url_for, request, session, flash
from ytmusicapi import YTMusic, OAuthCredentials
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from auth import spotify_bp, tidal_bp
from sync import sync_bp 
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")
app.config['UPLOAD_FOLDER'] = 'yt_headers'
# Register blueprints
app.register_blueprint(spotify_bp)
app.register_blueprint(tidal_bp)
# app.register_blueprint(youtube_bp)
app.register_blueprint(sync_bp)

YOUTUBE_API_ID = os.getenv("YOUTUBE_API_ID")
YOUTUBE_API_SECRET = os.getenv("YOUTUBE_API_SECRET")

tidal_session = None

@app.route('/')
def index():
    return render_template("index.html",
            logged_spotify='spotify_token_info' in session,
            logged_tidal='tidal_token' in session)


@app.route('/logout')
def logout():
    # Clear all stored tokens and session data
    keys_to_clear = [
        "spotify_token_info",'spotify_token', "access_token",'spotify_refresh_token',
        'tidal_token', 'tidal_refresh_token', "tidal_session_id", 'tidal_token_type', 'tidal_expiry',
        'youtube_auth'
    ]
    for key in keys_to_clear:
        session.pop(key, None)
    
    flash("✅ Has cerrado sesión correctamente.")
    return redirect(url_for('index'))


## ---- YouTube Music upload route DEBUG ---- ##

@app.route('/youtube/upload', methods=['GET', 'POST'])
def upload_youtube_headers():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("❌ No se envió ningún archivo.")
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash("❌ Nombre de archivo vacío.")
            return redirect(request.url)
        
        if file and file.filename.endswith('.json'):
            filename = secure_filename(file.filename)
            save_path = os.path.join('yt_headers', 'client_secret.json')
            file.save(save_path)

            # Test de autenticación inmediata
            try:
                from ytmusicapi import YTMusic
                # yt = YTMusic(save_path)
                yt = YTMusic(save_path, oauth_credentials=OAuthCredentials(client_id=YOUTUBE_API_ID, client_secret=YOUTUBE_API_SECRET))
                yt.get_liked_songs(limit=1)
                flash("✅ Archivo subido y autenticación con YouTube Music exitosa.")
            except Exception as e:
                flash(f"⚠️ Archivo subido, pero falló la autenticación: {e}")
            return redirect('/')
        else:
            flash("❌ Solo se permiten archivos .json")
            return redirect(request.url)
    else:
        return render_template("youtube_upload.html")
    

if __name__ == '__main__':
    print("🚀 Servidor Flask ejecutándose en http://localhost:5000")
    app.run(debug=True)

