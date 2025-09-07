# Spotify Playlist Downloader

A Python script that extracts track URLs from Spotify playlists and downloads them as MP3 files using spotDL.

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
   pip install -r requirements.txt
   ```

## Usage

### Basic URL extraction:
```bash
python3 spotify_playlist_extractor.py "https://open.spotify.com/playlist/PLAYLIST_ID"
```

### Download MP3 files:
```bash
python3 spotify_playlist_extractor.py "https://open.spotify.com/playlist/PLAYLIST_ID" --download
```

### Download with custom settings:
```bash
python3 spotify_playlist_extractor.py "playlist_url" --download --output-dir ~/Music/MyPlaylist --timeout 30
```

### Using the shell wrapper (easier):
```bash
./run_extractor.sh "playlist_url" --download
```

## Options

- `--download` - Download MP3 files using spotDL
- `--output-dir` - Specify download directory (default: parent folder of script)
- `--timeout` - Timeout per track in seconds (default: 20)
- `--overwrite` - How to handle existing files: `skip`, `force`, `prompt` (default: skip)
- `--format` - Output format for URLs: `urls`, `json`, `csv` (default: urls)
- `--info` - Show playlist information before processing

## Examples

```bash
# Just extract URLs
python3 spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"

# Download to current directory  
python3 spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download

# Download to specific folder with 30s timeout
python3 spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download --output-dir ~/Music/DJ --timeout 30

# Show playlist info and export as JSON
python3 spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --info --format json
```

## Notes

- **Public playlists only** - This script uses Client Credentials authentication which only works with public playlists
- **Liked songs** - Cannot access liked songs directly. Create a playlist from your liked songs and use that URL instead
- **Existing files** - By default, existing MP3 files are skipped to avoid re-downloading
- **Timeout protection** - Each track download has a timeout to prevent hanging on problematic tracks

## Troubleshooting

- **Authentication errors**: Check your `.env` file has correct Spotify credentials
- **spotDL not found**: Make sure dependencies are installed: `pip install -r requirements.txt`
- **Permission errors**: Make sure the output directory is writable
- **Playlist not found**: Ensure the playlist is public and the URL is correct
