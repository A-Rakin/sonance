// Audio player state
let audioPlayer = document.getElementById('audio-player');
let isPlaying = false;
let currentSong = null;
let playlist = [];
let currentIndex = -1;
let currentPlatform = 'local'; // 'local' or 'external'

// DOM elements
const playPauseBtn = document.getElementById('play-pause-btn');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const volumeSlider = document.getElementById('volume-slider');
const nowPlayingCover = document.getElementById('now-playing-cover');
const nowPlayingTitle = document.getElementById('now-playing-title');
const nowPlayingArtist = document.getElementById('now-playing-artist');

// Initialize player
function initPlayer() {
    if (!audioPlayer) {
        audioPlayer = document.getElementById('audio-player');
    }

    // Set volume from slider
    if (volumeSlider) {
        audioPlayer.volume = volumeSlider.value / 100;

        // Volume control
        volumeSlider.addEventListener('input', (e) => {
            audioPlayer.volume = e.target.value / 100;
        });
    }

    // Play/Pause button
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlay);
    }

    // Previous/Next buttons
    if (prevBtn) {
        prevBtn.addEventListener('click', playPrevious);
    }
    if (nextBtn) {
        nextBtn.addEventListener('click', playNext);
    }

    // Audio events
    audioPlayer.addEventListener('ended', playNext);
    audioPlayer.addEventListener('timeupdate', updateProgress);
    audioPlayer.addEventListener('loadedmetadata', function() {
        console.log('Audio loaded, duration:', this.duration);
        // Update total time display
        const totalTimeSpan = document.getElementById('total-time');
        if (totalTimeSpan && this.duration) {
            const minutes = Math.floor(this.duration / 60);
            const seconds = Math.floor(this.duration % 60);
            totalTimeSpan.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    });
    audioPlayer.addEventListener('error', function(e) {
        console.error('Audio error:', e);
        showNotification('Error playing song. File might be missing.', 'error');
    });
}

// Play song function (local database)
async function playSong(songId) {
    try {
        console.log('Attempting to play song:', songId);
        const response = await fetch(`/api/song/${songId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch song data');
        }
        const song = await response.json();
        console.log('Song data:', song);

        currentSong = song;
        currentPlatform = 'local';

        // Create audio element if it doesn't exist
        if (!audioPlayer) {
            audioPlayer = document.getElementById('audio-player');
            if (!audioPlayer) {
                audioPlayer = document.createElement('audio');
                audioPlayer.id = 'audio-player';
                document.body.appendChild(audioPlayer);
            }
        }

        // Set source and play
        audioPlayer.src = song.file_url;
        audioPlayer.load();

        // Update UI
        updateNowPlayingUI(song);

        // Play the song
        const playPromise = audioPlayer.play();
        if (playPromise !== undefined) {
            playPromise.then(() => {
                isPlaying = true;
                updatePlayPauseIcon();
                console.log('Playback started successfully');
                showNotification(`Now playing: ${song.title}`, 'success');
            }).catch(error => {
                console.error('Playback failed:', error);
                showNotification('Failed to play song. Please check if the audio file exists.', 'error');
            });
        }

        // Add to playlist if not already there
        if (!playlist.some(item => item.id === songId)) {
            playlist.push({ id: songId, type: 'local' });
            currentIndex = playlist.length - 1;
        }

    } catch (error) {
        console.error('Error playing song:', error);
        showNotification('Error loading song. Please try again.', 'error');
    }
}

// Play external song from Deezer
async function playExternalSong(songData) {
    try {
        showNotification('Loading from Deezer...', 'info');

        // Parse song data if it's a string
        let song;
        if (typeof songData === 'string') {
            song = JSON.parse(songData);
        } else {
            song = songData;
        }

        console.log('Playing Deezer song:', song);

        // Deezer provides preview URLs directly
        if (song.preview) {
            // Create song object for player
            const tempSong = {
                id: 'deezer-' + (song.id || Date.now()),
                title: song.title || song.name,
                artist: song.artist,
                album: song.album || 'Deezer Track',
                duration: song.duration || 30,
                file_url: song.preview,  // Direct preview URL from Deezer
                cover_url: song.cover || song.cover_medium || song.cover_big || '/static/default-album.jpg',
                platform: 'deezer',
                isExternal: true,
                originalData: song
            };

            currentSong = tempSong;
            currentPlatform = 'external';

            // Set source and play
            audioPlayer.src = tempSong.file_url;
            audioPlayer.load();

            // Update UI
            updateNowPlayingUI(tempSong);

            // Play
            audioPlayer.play()
                .then(() => {
                    isPlaying = true;
                    updatePlayPauseIcon();
                    showNotification(`Now playing: ${tempSong.title} from Deezer`, 'success');
                })
                .catch(error => {
                    console.error('Playback failed:', error);
                    showNotification('Failed to play Deezer stream. Try another song.', 'error');
                });

            // Add to playlist
            playlist.push(tempSong);
            currentIndex = playlist.length - 1;
        } else {
            showNotification('No preview available for this song on Deezer', 'error');
        }

    } catch (error) {
        console.error('Error playing Deezer song:', error);
        showNotification('Failed to play song from Deezer', 'error');
    }
}

// Update Now Playing UI
function updateNowPlayingUI(song) {
    if (nowPlayingCover) {
        nowPlayingCover.src = song.cover_url || song.cover || '/static/default-album.jpg';
    }
    if (nowPlayingTitle) {
        nowPlayingTitle.textContent = song.title || song.name;
    }
    if (nowPlayingArtist) {
        nowPlayingArtist.textContent = song.artist;
    }

    // Update player page elements if they exist
    const playerTitle = document.getElementById('player-title');
    const playerArtist = document.getElementById('player-artist');
    const playerAlbum = document.getElementById('player-album');
    const playerCover = document.getElementById('player-cover');

    if (playerTitle) playerTitle.textContent = song.title || song.name;
    if (playerArtist) playerArtist.textContent = song.artist;
    if (playerAlbum) playerAlbum.textContent = song.album || 'Deezer Track';
    if (playerCover) playerCover.src = song.cover_url || song.cover || '/static/default-album.jpg';

    // Update platform indicator
    const platformIndicator = document.getElementById('platform-indicator');
    if (platformIndicator) {
        if (song.isExternal) {
            platformIndicator.innerHTML = `<i class="fas fa-globe"></i> Deezer`;
            platformIndicator.style.display = 'inline-flex';
        } else {
            platformIndicator.style.display = 'none';
        }
    }
}

// Toggle play/pause
function togglePlay() {
    if (!currentSong) {
        showNotification('No song selected', 'info');
        return;
    }

    if (audioPlayer.paused) {
        audioPlayer.play()
            .then(() => {
                isPlaying = true;
                updatePlayPauseIcon();
            })
            .catch(error => {
                console.error('Play failed:', error);
                showNotification('Failed to play. Please try again.', 'error');
            });
    } else {
        audioPlayer.pause();
        isPlaying = false;
        updatePlayPauseIcon();
    }
}

// Update play/pause icon
function updatePlayPauseIcon() {
    const playPauseBtn = document.getElementById('play-pause-btn');
    const playPauseLarge = document.getElementById('play-pause-large');

    if (playPauseBtn) {
        const icon = playPauseBtn.querySelector('i');
        if (icon) {
            icon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
        }
    }

    if (playPauseLarge) {
        const icon = playPauseLarge.querySelector('i');
        if (icon) {
            icon.className = isPlaying ? 'fas fa-pause' : 'fas fa-play';
        }
    }
}

// Play previous song
function playPrevious() {
    if (playlist.length > 0 && currentIndex > 0) {
        currentIndex--;
        const item = playlist[currentIndex];
        if (item.type === 'local') {
            playSong(item.id);
        } else {
            playExternalSong(item.originalData);
        }
    }
}

// Play next song
function playNext() {
    if (playlist.length > 0 && currentIndex < playlist.length - 1) {
        currentIndex++;
        const item = playlist[currentIndex];
        if (item.type === 'local') {
            playSong(item.id);
        } else {
            playExternalSong(item.originalData);
        }
    } else if (playlist.length > 0) {
        // Loop back to first song
        currentIndex = 0;
        const item = playlist[currentIndex];
        if (item.type === 'local') {
            playSong(item.id);
        } else {
            playExternalSong(item.originalData);
        }
    }
}

// Update progress bar
function updateProgress() {
    const progressFill = document.getElementById('progress-fill');
    const currentTimeSpan = document.getElementById('current-time');

    if (progressFill && audioPlayer.duration) {
        const progress = (audioPlayer.currentTime / audioPlayer.duration) * 100;
        progressFill.style.width = progress + '%';
    }

    if (currentTimeSpan && audioPlayer.currentTime) {
        const minutes = Math.floor(audioPlayer.currentTime / 60);
        const seconds = Math.floor(audioPlayer.currentTime % 60);
        currentTimeSpan.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
}

// Search functionality with Deezer API
const searchInput = document.getElementById('search-input');
if (searchInput) {
    let searchTimeout;

    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch(e.target.value);
        }, 300);
    });
}

async function performSearch(query) {
    if (!query.trim()) return;

    try {
        // Search local database
        const localResponse = await fetch(`/search?q=${encodeURIComponent(query)}`);
        const localResults = await localResponse.json();

        // Search Deezer API
        let deezerResults = { data: [] };
        try {
            const deezerResponse = await fetch(`/api/music/search?q=${encodeURIComponent(query)}&platform=deezer&limit=8`);
            deezerResults = await deezerResponse.json();
            console.log('Deezer results:', deezerResults);
        } catch (error) {
            console.log('Deezer search not available:', error);
        }

        displaySearchResults(localResults, deezerResults);
    } catch (error) {
        console.error('Search error:', error);
    }
}

function displaySearchResults(localResults, deezerResults) {
    // Remove old results
    const oldResults = document.querySelector('.search-results');
    if (oldResults) oldResults.remove();

    let resultsHTML = '<div class="search-results">';

    // Add platform filter buttons
    resultsHTML += `
        <div class="search-filters">
            <button class="filter-btn active" data-filter="all">All</button>
            <button class="filter-btn" data-filter="local">My Library</button>
            <button class="filter-btn" data-filter="deezer">Deezer</button>
        </div>
    `;

    // Display local results
    if (localResults.songs && localResults.songs.length > 0) {
        resultsHTML += '<h4 class="local-header">📚 Your Library</h4>';
        localResults.songs.slice(0, 5).forEach(song => {
            resultsHTML += `
                <div class="search-result-item local-song" data-filter="local" onclick="playSong(${song.id})">
                    <i class="fas fa-music"></i>
                    <div class="result-info">
                        <span class="title">${escapeHtml(song.title)}</span>
                        <span class="artist">${escapeHtml(song.artist)}</span>
                    </div>
                    <span class="badge local">Library</span>
                </div>
            `;
        });
    }

    // Display Deezer results
    if (deezerResults.data && deezerResults.data.length > 0) {
        resultsHTML += '<h4 class="deezer-header">🎵 Deezer</h4>';
        deezerResults.data.slice(0, 8).forEach(song => {
            resultsHTML += `
                <div class="search-result-item deezer-song" data-filter="deezer"
                     onclick='playExternalSong(${JSON.stringify(song).replace(/'/g, "&apos;")})'>
                    <img src="${song.cover_small || song.cover || '/static/default-album.jpg'}"
                         class="result-thumbnail"
                         onerror="this.src='/static/default-album.jpg'">
                    <div class="result-info">
                        <span class="title">${escapeHtml(song.title)}</span>
                        <span class="artist">${escapeHtml(song.artist)}</span>
                    </div>
                    <span class="badge deezer">Deezer</span>
                </div>
            `;
        });
    }

    if ((!localResults.songs || localResults.songs.length === 0) &&
        (!deezerResults.data || deezerResults.data.length === 0)) {
        resultsHTML += '<p class="no-results">No results found</p>';
    }

    resultsHTML += '</div>';

    // Add results to page
    if (searchInput) {
        searchInput.parentElement.insertAdjacentHTML('afterend', resultsHTML);

        // Add filter functionality
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                const filter = this.dataset.filter;

                // Update active button
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                // Filter results
                document.querySelectorAll('.search-result-item').forEach(item => {
                    if (filter === 'all') {
                        item.style.display = 'flex';
                    } else {
                        const itemFilter = item.classList.contains('local-song') ? 'local' :
                                          item.classList.contains('deezer-song') ? 'deezer' : null;
                        item.style.display = itemFilter === filter ? 'flex' : 'none';
                    }
                });
            });
        });
    }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Favorite functionality
async function toggleFavorite(songId, button) {
    try {
        const response = await fetch(`/favorite/toggle/${songId}`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            const icon = button.querySelector('i');
            if (data.is_favorite) {
                icon.className = 'fas fa-heart';
                button.style.background = 'var(--primary)';
                showNotification('Added to favorites', 'success');
            } else {
                icon.className = 'far fa-heart';
                button.style.background = '';
                showNotification('Removed from favorites', 'info');
            }
        }
    } catch (error) {
        console.error('Error toggling favorite:', error);
    }
}

// Create playlist
async function createPlaylist() {
    const name = prompt('Enter playlist name:');
    if (!name) return;

    try {
        const response = await fetch('/playlist/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ name })
        });

        const data = await response.json();
        if (data.success) {
            showNotification('Playlist created successfully!', 'success');
            // Reload playlists if function exists
            if (typeof loadUserPlaylists === 'function') {
                loadUserPlaylists();
            }
        }
    } catch (error) {
        console.error('Error creating playlist:', error);
        showNotification('Failed to create playlist', 'error');
    }
}

// Add to playlist
async function addToPlaylist(playlistId, songId) {
    try {
        const response = await fetch(`/playlist/${playlistId}/add-song`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ song_id: songId })
        });

        const data = await response.json();
        if (data.success) {
            showNotification('Song added to playlist!', 'success');
            closeModal();
        }
    } catch (error) {
        console.error('Error adding to playlist:', error);
        showNotification('Failed to add to playlist', 'error');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;

    const icon = type === 'info' ? 'info-circle' :
                 type === 'success' ? 'check-circle' :
                 'exclamation-circle';

    notification.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;

    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Close modal
function closeModal() {
    const modal = document.getElementById('playlist-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Seek in audio
function seekAudio(event) {
    const progressBar = event.currentTarget;
    const rect = progressBar.getBoundingClientRect();
    const clickPosition = (event.clientX - rect.left) / rect.width;
    audioPlayer.currentTime = clickPosition * audioPlayer.duration;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initPlayer();

    // Close search results when clicking outside
    document.addEventListener('click', (e) => {
        const results = document.querySelector('.search-results');
        const searchInput = document.getElementById('search-input');
        if (results && searchInput && !results.contains(e.target) && !searchInput.contains(e.target)) {
            results.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                results.remove();
            }, 300);
        }
    });

    // Add seek functionality to progress bar
    const progressBar = document.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.addEventListener('click', seekAudio);
    }
});

// Export functions for global use
window.playSong = playSong;
window.playExternalSong = playExternalSong;
window.toggleFavorite = toggleFavorite;
window.createPlaylist = createPlaylist;
window.addToPlaylist = addToPlaylist;
window.togglePlay = togglePlay;
window.playPrevious = playPrevious;
window.playNext = playNext;
window.closeModal = closeModal;
window.showNotification = showNotification;