# 🎵 Sonance - Modern Music Library Web App

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.8+-yellow)
![Flask](https://img.shields.io/badge/flask-2.0+-black)


Sonance is a beautiful, feature-rich music library management web application built with Flask. It allows users to manage songs, albums, artists, playlists, and search for music with a stunning glass-morphism UI.

## ✨ Features

- 🎨 **Beautiful Glass-morphism UI** - Modern, translucent design with blur effects
- 🔍 **Advanced Search** - Search your local library and Deezer's global catalog
- ▶️ **Music Player** - Built-in audio player with play/pause, next/previous controls
- 📚 **Library Management** - Manage songs, albums, artists, and playlists
- ❤️ **Favorites** - Mark songs as favorites for quick access
- 📊 **Statistics Dashboard** - View your music library statistics
- 🌐 **Deezer Integration** - Search and preview songs from Deezer's 73M+ track catalog
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript
- **Icons**: Font Awesome 6
- **Music API**: Deezer Public API
- **Authentication**: Flask-Login

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Node.js (optional, for future enhancements)
- Internet connection (for Deezer API)

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/sonance.git
cd sonance
```

### 🎯 SONANCE USAGE GUIDE

🔐 AUTHENTICATION
Register

• Create a new account

• Run: python app.py create-user (or use web interface)

Login

• Access your personal library

• Default admin: admin / admin123


Guest Mode

• Browse public content without login

🎵 PLAYING MUSIC

Local Songs:

• Click on any song card's play button

• Songs play in the bottom player bar


Deezer Songs:

• Search for any artist or song

• Click on Deezer results to play 30-second previews


📚 MANAGING LIBRARY

Add Songs

• Upload your own audio files (MP3, WAV, OGG)

• Max file size: 50MB


Create Playlists

• Organize songs into custom playlists

• Command: curl -X POST /playlist/create


Favorite Songs

• Click heart icon to save favorites

• View at: /favorites

View Stats

• See total songs, plays, and more

• API: /api/stats


🔍 SEARCH FEATURES
• Search local library - Quick search across your collection

• Search Deezer's global catalog - Access 73M+ tracks

• Filter results by source - Local / Deezer

• Click results to play instantly

• API: /api/music/search?q=your_query


🌐 DEEZER API INTEGRATION
• Global Music Catalog - Search across 73M+ tracks

• 30-Second Previews - Preview any song before adding

• Album Art & Artist Info - Rich metadata for all tracks

• Trending & Popular - Access charts and trending music

• ✨ No API key required! Deezer's public endpoints work out of the box

<img width="1365" height="585" alt="image" src="https://github.com/user-attachments/assets/3e9c1300-2fec-49c1-b11d-cab0bd97fff8" />
<img width="1356" height="604" alt="image" src="https://github.com/user-attachments/assets/c79d373e-04dd-43a2-ad21-be275dea8456" />
<img width="1363" height="549" alt="image" src="https://github.com/user-attachments/assets/126a4dcd-e9be-4954-82d0-e6d4be4fa005" />


