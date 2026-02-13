from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# Association tables for many-to-many relationships
playlist_songs = db.Table('playlist_songs',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default='default-avatar.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    playlists = db.relationship('Playlist', backref='owner', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

class Artist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)
    image = db.Column(db.String(200), default='default-artist.jpg')
    albums = db.relationship('Album', backref='artist', lazy=True)
    songs = db.relationship('Song', backref='artist', lazy=True)

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    release_date = db.Column(db.Date)
    cover_image = db.Column(db.String(200), default='default-album.jpg')
    genre = db.Column(db.String(50))
    songs = db.relationship('Song', backref='album', lazy=True)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    duration = db.Column(db.Integer)  # in seconds
    file_path = db.Column(db.String(200), nullable=False)
    plays = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cover_image = db.Column(db.String(200), default='default-playlist.jpg')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    songs = db.relationship('Song', secondary=playlist_songs, lazy='subquery',
                           backref=db.backref('playlists', lazy=True))

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey('song.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)