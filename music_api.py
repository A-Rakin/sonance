import deezer


class MusicAPIService:
    def __init__(self):
        """Initialize Deezer client - no API key needed for public endpoints!"""
        self.client = deezer.Client()

    def search_tracks(self, query, limit=10):
        """Search for tracks on Deezer"""
        try:
            results = self.client.search(query)
            tracks = []
            for track in list(results)[:limit]:
                tracks.append({
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artist.name,
                    'artist_id': track.artist.id,
                    'album': track.album.title,
                    'album_id': track.album.id,
                    'cover': track.album.cover_medium,
                    'cover_small': track.album.cover_small,
                    'cover_big': track.album.cover_big,
                    'preview': track.preview,  # 30-second preview URL
                    'duration': track.duration,
                    'platform': 'deezer'
                })
            return {'data': tracks, 'platform': 'deezer'}
        except Exception as e:
            return {'error': str(e)}

    def get_track(self, track_id):
        """Get specific track details"""
        try:
            track = self.client.get_track(track_id)
            return {
                'id': track.id,
                'title': track.title,
                'artist': track.artist.name,
                'artist_id': track.artist.id,
                'album': track.album.title,
                'album_id': track.album.id,
                'cover': track.album.cover_medium,
                'preview': track.preview,
                'duration': track.duration,
                'platform': 'deezer'
            }
        except Exception as e:
            return {'error': str(e)}

    def get_artist_top_tracks(self, artist_id, limit=5):
        """Get top tracks for an artist"""
        try:
            artist = self.client.get_artist(artist_id)
            tracks = artist.get_top()
            result = []
            for track in list(tracks)[:limit]:
                result.append({
                    'id': track.id,
                    'title': track.title,
                    'artist': track.artist.name,
                    'preview': track.preview
                })
            return {'data': result}
        except Exception as e:
            return {'error': str(e)}

    def get_trending(self):
        """Get trending tracks (charts)"""
        try:
            # Deezer doesn't have direct charts method in library
            # Using search as fallback
            return self.search_tracks("trending", 10)
        except Exception as e:
            return {'error': str(e)}