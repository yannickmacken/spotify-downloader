# Spotify Playlist Downloader

A Python script that extracts track URLs from Spotify playlists and downloads them as MP3 files using spotDL.

## Quick Start

If you already have the dependencies installed and configured:

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run the script
python spotify_playlist_extractor.py "https://open.spotify.com/playlist/YOUR_PLAYLIST_ID" --download
```

## Prerequisites

1. **Python 3.6+** installed on your system
2. **Spotify App** registered at [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## Setup

1. **Clone/Download** this script folder to your computer

2. **Get Spotify API Credentials:**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Create a new app
   - Copy your `Client ID` and `Client Secret`

3. **Configure credentials** in the `.env` file:
   ```
   SPOTIFY-CLIENT-ID=your_client_id_here
   SPOTIFY-CLIENT-SECRET=your_client_secret_here
   ```

4. **Install dependencies** (including spotDL):
   ```bash
   # Create a virtual environment (recommended)
   python3 -m venv venv
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

## Usage

**Note:** If you installed dependencies in a virtual environment, activate it first:
```bash
source venv/bin/activate
```

### Basic URL extraction:
```bash
python spotify_playlist_extractor.py "https://open.spotify.com/playlist/PLAYLIST_ID"
```

### Download MP3 files:
```bash
python spotify_playlist_extractor.py "https://open.spotify.com/playlist/PLAYLIST_ID" --download
```

### Download with custom settings:
```bash
python spotify_playlist_extractor.py "playlist_url" --download --output-dir ~/Music/MyPlaylist --timeout 30
```

### Alternative: Run directly with venv Python (no activation needed):
```bash
venv/bin/python spotify_playlist_extractor.py "playlist_url" --download
```

## Options

- `--download` - Download MP3 files using spotDL
- `--output-dir` - Specify download directory (default: parent folder of script)
- `--timeout` - Timeout per track in seconds (default: 20)
- `--overwrite` - How to handle existing files: `skip`, `force`, `prompt` (default: skip)
- `--format` - Output format for URLs: `urls`, `json`, `csv` (default: urls)
- `--info` - Show playlist information before processing
- `--added-after` - Only include tracks added to playlist after specified date (format: YYYY-MM-DD, excludes the specified date)

## Examples

```bash
# Just extract URLs
python spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Download to current directory  
python spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download

# Download to specific folder with 30s timeout
python spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download --output-dir ~/Music/DJ --timeout 30

# Show playlist info and export as JSON
python spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --info --format json

# Download only tracks added after January 1, 2024 (excludes Jan 1st itself)
python spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download --added-after 2024-01-01
```

## Notes

- **Public playlists only** - This script uses Client Credentials authentication which only works with public playlists
- **Liked songs** - Cannot access liked songs directly. Create a playlist from your liked songs and use that URL instead
- **Existing files** - By default, existing MP3 files are skipped to avoid re-downloading
- **Timeout protection** - Each track download has a timeout to prevent hanging on problematic tracks
- **Date filtering** - The `--added-after` parameter excludes tracks added on the specified date itself (strictly "after")

## Troubleshooting

- **Authentication errors**: Check your `.env` file has correct Spotify credentials
- **spotDL not found**: Make sure dependencies are installed: `pip install -r requirements.txt`
- **Permission errors**: Make sure the output directory is writable
- **Playlist not found**: Ensure the playlist is public and the URL is correct
