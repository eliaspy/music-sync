from flask import Blueprint, render_template, request, session, redirect, flash, url_for
from auth.spotify_auth import get_spotify_client
from auth.tidal_auth import get_tidal_session
import sys
import os 
import tidalapi
sync_bp = Blueprint('sync', __name__, url_prefix='/sync')


@sync_bp.route('/choose-playlist', methods=['GET', 'POST'])
def choose_playlist():
    if 'spotify_token_info' not in session or 'tidal_token' not in session:
        flash("⚠️ Primero debes autenticarte en Spotify y Tidal.")
        return redirect('/')
    sp = get_spotify_client()
    playlists = get_spotify_playlists(sp)
    return render_template("choose_playlist.html", playlists=playlists)

@sync_bp.route('/perform', methods=['POST'])
def perform_sync():
    if 'spotify_token_info' not in session or 'tidal_session_id' not in session:
        flash("⚠️ Primero debes autenticarte en Spotify y Tidal.")
        return redirect('/')
    try:
        sp = get_spotify_client()
        td = get_tidal_session()
        playlist_id = request.form['spotify_playlist_id']
        playlist_name = sp.playlist(playlist_id)['name']
        tracks = get_tracks_from_spotify_playlist(sp, playlist_id)
        existing_playlists = td.user.playlists()
        for tidal_playlist in existing_playlists:
            if tidal_playlist.name.strip().lower() == playlist_name.strip().lower():
                print(f"⚠️ Playlist '{playlist_name}' ya existe en Tidal (ID: {tidal_playlist.id}) evaluar si hay tracks nuevos...")
                re_sync(tidal_playlist, td, tracks)
                return redirect('/')
        tidal_playlist = td.user.create_playlist(
        playlist_name,
            "Sincronizada desde Spotify"  # Descripción
        )
        print(f"✅ Playlist creada en Tidal: {playlist_name} (ID: {tidal_playlist.id})")
        add_tracks_to_tidal_playlist(tidal_playlist,td, tracks)
        
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        flash(f"❌ Error en sincronización: {e} , Tipo: {exc_type}, Archivo: {fname}, Línea: {exc_tb.tb_lineno}")

    return redirect('/')

## sync_spotify_playlist_to_tidal
# Esta ruta sincroniza una playlist de Spotify a Tidal.

def get_spotify_playlists(sp):
    playlists = sp.current_user_playlists(limit=50)
    return [(p['name'], p['id']) for p in playlists['items']]

def get_tracks_from_spotify_playlist(sp, playlist_id):
    tracks = []
    offset = 0
    limit = 100
    while True:
        response = sp.playlist_tracks(playlist_id, limit=limit, offset=offset)
        items = response['items']
        if not items:
            break
        for item in items:
            track = item.get('track')
            if track:
                title = track.get('name')
                artists = track.get('artists', [])
                artist_name = artists[0]['name']
                tracks.append((title, artist_name))
        offset += limit
        if offset >= response['total']:
            break
    print(f"Found {len(tracks)} tracks in Spotify playlist '{playlist_id}'")
    return tracks

def add_tracks_to_tidal_playlist(tidal_playlist,tidal_session, tracks):
    track_len = len(tracks)
    count = 0
    print("tidal_playlist:", tidal_playlist.name, tidal_playlist.id)

    for title, artist in tracks:
        search_results = tidal_playlist.session.search(
            f"{title} {artist}",
            models=[tidalapi.Track]
        )['tracks']

        if search_results:
            track_id = search_results[0].id
            print(f"Adding track {title} - {artist} (ID: {track_id})")
            tidal_playlist.add([track_id])
            count += 1
        else:
            flash(f"⚠️ Algunos tracks no se encontraron en Tidal: {title} - {artist}")
            print(f"❌ No match found for: {title} - {artist}")
    print(f"✅ {count}/{track_len} canciones agregadas '{tidal_playlist.name}'")
    flash(f"✅ Sincronización completa: {count}/{track_len} canciones agregadas a '{tidal_playlist.name}'")
    return

def re_sync(tidal_playlist, tidal_session, tracks):
    track_len = len(tracks)
    count = 0
    existing_tracks = tidal_playlist.tracks()
    existing_track_ids = {track.id for track in existing_tracks}
    for title, artist in tracks:
        search_results = tidal_session.search(f"{title} {artist}", models=[tidalapi.Track])['tracks']
        if search_results:
            track_id = search_results[0].id
            if track_id not in existing_track_ids:
                tidal_playlist.add([track_id])
                added_count += 1
                print(f"✅ Canción sincronizada en playlist: {title} - {artist}")
        else:
            print(f"❌ No encontrada en Tidal: {title} - {artist}")

    print(f"✅ {count}/{track_len} canciones agregadas '{tidal_playlist.name}'")
    flash(f"✅ Sincronización completa: {count}/{track_len} canciones agregadas a '{tidal_playlist.name}'")
    return