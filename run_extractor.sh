#!/bin/bash
# Spotify Playlist Extractor Runner
# This script activates the virtual environment and runs the playlist extractor

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the script with all arguments passed through
python spotify_playlist_extractor.py "$@"
