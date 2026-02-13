import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Artist, Album, Song, Playlist, Favorite
from datetime import datetime
import json
from music_api import MusicAPIService

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload directories exist
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'audio'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'covers'), exist_ok=True)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Allowed file extensions
ALLOWED_AUDIO = {'mp3', 'wav', 'ogg', 'm4a'}
ALLOWED_IMAGES = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set


# Routes
@app.route('/')
def index():
    featured_songs = Song.query.order_by(Song.plays.desc()).limit(10).all()
    recent_albums = Album.query.order_by(Album.release_date.desc()).limit(6).all()

    # Fix for the popular artists query
    popular_artists = Artist.query.limit(6).all()

    return render_template('index.html',
                           featured_songs=featured_songs,
                           recent_albums=recent_albums,
                           popular_artists=popular_artists)


@app.route('/library')
def library():
    songs = Song.query.all()
    albums = Album.query.all()
    artists = Artist.query.all()
    return render_template('library.html',
                           songs=songs,
                           albums=albums,
                           artists=artists)


@app.route('/search')
def search():
    query = request.args.get('q', '')
    if query:
        songs = Song.query.filter(Song.title.contains(query)).all()
        artists = Artist.query.filter(Artist.name.contains(query)).all()
        albums = Album.query.filter(Album.title.contains(query)).all()
    else:
        songs = artists = albums = []

    return jsonify({
        'songs': [{'id': s.id, 'title': s.title, 'artist': s.artist.name if s.artist else 'Unknown'} for s in songs],
        'artists': [{'id': a.id, 'name': a.name} for a in artists],
        'albums': [{'id': a.id, 'title': a.title, 'artist': a.artist.name if a.artist else 'Unknown'} for a in albums]
    })


@app.route('/player/<int:song_id>')
def player(song_id):
    song = Song.query.get_or_404(song_id)
    song.plays += 1
    db.session.commit()
    return render_template('player.html', song=song)


@app.route('/api/song/<int:song_id>')
def get_song(song_id):
    song = Song.query.get_or_404(song_id)
    return jsonify({
        'id': song.id,
        'title': song.title,
        'artist': song.artist.name if song.artist else 'Unknown',
        'album': song.album.title if song.album else 'Single',
        'duration': song.duration,
        'file_url': url_for('static', filename=f'uploads/audio/{song.file_path}'),
        'cover_url': url_for('static',
                             filename=f'uploads/covers/{song.album.cover_image}') if song.album and song.album.cover_image else url_for(
            'static', filename='default-album.jpg')
    })


@app.route('/playlist/create', methods=['POST'])
@login_required
def create_playlist():
    data = request.get_json()
    playlist = Playlist(
        name=data['name'],
        description=data.get('description', ''),
        user_id=current_user.id
    )
    db.session.add(playlist)
    db.session.commit()
    return jsonify({'success': True, 'id': playlist.id})


@app.route('/playlist/<int:playlist_id>/add-song', methods=['POST'])
@login_required
def add_to_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json()
    song = Song.query.get(data['song_id'])
    if song and song not in playlist.songs:
        playlist.songs.append(song)
        db.session.commit()

    return jsonify({'success': True})


@app.route('/favorite/toggle/<int:song_id>', methods=['POST'])
@login_required
def toggle_favorite(song_id):
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        song_id=song_id
    ).first()

    if favorite:
        db.session.delete(favorite)
        is_favorite = False
    else:
        favorite = Favorite(user_id=current_user.id, song_id=song_id)
        db.session.add(favorite)
        is_favorite = True

    db.session.commit()
    return jsonify({'success': True, 'is_favorite': is_favorite})


@app.route('/api/upload', methods=['POST'])
@login_required
def upload_song():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    cover_file = request.files.get('cover')

    if audio_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if audio_file and allowed_file(audio_file.filename, ALLOWED_AUDIO):
        # Save audio file
        audio_filename = secure_filename(audio_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', audio_filename)
        audio_file.save(audio_path)

        # Save cover if provided
        cover_filename = 'default-album.jpg'
        if cover_file and allowed_file(cover_file.filename, ALLOWED_IMAGES):
            cover_filename = secure_filename(cover_file.filename)
            cover_path = os.path.join(app.config['UPLOAD_FOLDER'], 'covers', cover_filename)
            cover_file.save(cover_path)

        # Get or create artist
        artist_name = request.form.get('artist', 'Unknown Artist')
        artist = Artist.query.filter_by(name=artist_name).first()
        if not artist:
            artist = Artist(name=artist_name)
            db.session.add(artist)
            db.session.flush()

        # Get or create album
        album_title = request.form.get('album', 'Singles')
        album = Album.query.filter_by(title=album_title, artist_id=artist.id).first()
        if not album and album_title:
            album = Album(
                title=album_title,
                artist_id=artist.id,
                cover_image=cover_filename,
                genre=request.form.get('genre', 'Unknown')
            )
            db.session.add(album)
            db.session.flush()

        # Create song
        song = Song(
            title=request.form.get('title', 'Untitled'),
            artist_id=artist.id,
            album_id=album.id if album else None,
            duration=int(request.form.get('duration', 0)),
            file_path=audio_filename
        )

        db.session.add(song)
        db.session.commit()

        return jsonify({'success': True, 'song_id': song.id})

    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/stats')
def get_stats():
    total_songs = Song.query.count()
    total_artists = Artist.query.count()
    total_albums = Album.query.count()
    total_plays = db.session.query(db.func.sum(Song.plays)).scalar() or 0

    return jsonify({
        'songs': total_songs,
        'artists': total_artists,
        'albums': total_albums,
        'plays': total_plays
    })


@app.route('/api/playlists')
@login_required
def get_playlists():
    playlists = Playlist.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'description': p.description,
        'song_count': len(p.songs)
    } for p in playlists])


# Simple login route for testing (you'll want to expand this)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Simple login logic - expand as needed
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Create default admin user if none exists
@app.cli.command("create-admin")
def create_admin():
    """Create admin user"""
    with app.app_context():
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print('Admin user created!')

# Add to app.py
@app.route('/static/default-avatar.png')
def default_avatar():
    return send_file('static/default-avatar.png', mimetype='image/png')


@app.route('/discover')
def discover():
    return render_template('discover.html')


@app.route('/favorites')
@login_required
def favorites():
    return render_template('favorites.html')


@app.route('/api/songs/trending')
def get_trending_songs():
    songs = Song.query.order_by(Song.plays.desc()).limit(10).all()
    return jsonify([{
        'id': s.id,
        'title': s.title,
        'artist': s.artist.name if s.artist else 'Unknown',
        'cover_url': url_for('static',
                             filename=f'uploads/covers/{s.album.cover_image}') if s.album and s.album.cover_image else url_for(
            'static', filename='default-album.jpg')
    } for s in songs])


@app.route('/api/albums/new-releases')
def get_new_releases():
    albums = Album.query.order_by(Album.release_date.desc()).limit(10).all()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'artist': a.artist.name if a.artist else 'Unknown',
        'cover_url': url_for('static', filename=f'uploads/covers/{a.cover_image}') if a.cover_image else url_for(
            'static', filename='default-album.jpg')
    } for a in albums])


@app.route('/api/songs/recommended')
@login_required
def get_recommended_songs():
    # Simple recommendation based on user's favorites
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    favorite_artist_ids = [f.song.artist_id for f in favorites if f.song and f.song.artist]

    if favorite_artist_ids:
        # Get songs from favorite artists
        songs = Song.query.filter(Song.artist_id.in_(favorite_artist_ids)).order_by(Song.plays.desc()).limit(10).all()
    else:
        # If no favorites, return popular songs
        songs = Song.query.order_by(Song.plays.desc()).limit(10).all()

    return jsonify([{
        'id': s.id,
        'title': s.title,
        'artist': s.artist.name if s.artist else 'Unknown',
        'cover_url': url_for('static',
                             filename=f'uploads/covers/{s.album.cover_image}') if s.album and s.album.cover_image else url_for(
            'static', filename='default-album.jpg')
    } for s in songs])


@app.route('/api/artists/popular')
def get_popular_artists():
    artists = Artist.query.limit(10).all()
    return jsonify([{
        'id': a.id,
        'name': a.name,
        'image_url': url_for('static', filename=f'uploads/covers/{a.image}') if a.image else url_for('static',
                                                                                                     filename='default-artist.jpg'),
        'songs_count': len(a.songs)
    } for a in artists])


@app.route('/api/user/recently-played')
@login_required
def get_recently_played():
    # This would need a RecentPlay model - for now return empty list
    return jsonify([])


@app.route('/api/user/favorites')
@login_required
def get_user_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc()).all()
    return jsonify({
        'favorites': [{
            'id': f.song.id,
            'title': f.song.title,
            'artist': f.song.artist.name if f.song.artist else 'Unknown',
            'duration': f.song.duration,
            'plays': f.song.plays,
            'cover_url': url_for('static',
                                 filename=f'uploads/covers/{f.song.album.cover_image}') if f.song.album and f.song.album.cover_image else url_for(
                'static', filename='default-album.jpg'),
            'added_date': f.created_at.strftime('%Y-%m-%d')
        } for f in favorites]
    })


@app.route('/api/song/<int:song_id>/stream')
def stream_song(song_id):
    song = Song.query.get_or_404(song_id)
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio', song.file_path)

    if not os.path.exists(audio_path):
        return jsonify({'error': 'Audio file not found'}), 404

    return send_file(audio_path, mimetype='audio/mpeg')


from flask import flash


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validation
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters')
            return render_template('register.html')

        # Check if user exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists')
            return render_template('register.html')

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered')
            return render_template('register.html')

        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except:
            flash('An error occurred. Please try again.')
            return render_template('register.html')

    return render_template('register.html')

@app.route('/playlist/<int:playlist_id>')
def view_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    return render_template('playlist.html', playlist=playlist)


# View a single playlist
@app.route('/playlist/<int:playlist_id>')
def playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    return render_template('playlist.html', playlist=playlist)

# Remove song from playlist
@app.route('/playlist/<int:playlist_id>/remove-song', methods=['POST'])
@login_required
def remove_from_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json()
    song = Song.query.get(data['song_id'])
    if song in playlist.songs:
        playlist.songs.remove(song)
        db.session.commit()

    return jsonify({'success': True})


# Edit playlist
@app.route('/playlist/<int:playlist_id>/edit', methods=['POST'])
@login_required
def edit_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    data = request.get_json()
    playlist.name = data.get('name', playlist.name)
    playlist.description = data.get('description', playlist.description)
    db.session.commit()

    return jsonify({'success': True})


# Delete playlist
@app.route('/playlist/<int:playlist_id>/delete', methods=['POST'])
@login_required
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)
    if playlist.user_id != current_user.id:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    db.session.delete(playlist)
    db.session.commit()

    return jsonify({'success': True})


# Initialize the simple music API service
music_api = MusicAPIService()


@app.route('/api/music/search')
def music_search_simple():
    """Search for music using Deezer"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))

    if not query:
        return jsonify({'error': 'No search query'}), 400

    try:
        results = music_api.search_tracks(query, limit)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/music/track/<int:track_id>')
def get_track_info(track_id):
    """Get track details"""
    try:
        track = music_api.get_track(track_id)
        return jsonify(track)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/music/trending')
def get_trending_music():
    """Get trending tracks"""
    try:
        results = music_api.get_trending()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/music/artist/<int:artist_id>/top')
def get_artist_top(artist_id):
    """Get artist's top tracks"""
    try:
        results = music_api.get_artist_top_tracks(artist_id)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)