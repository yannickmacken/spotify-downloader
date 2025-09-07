#!/usr/bin/env python3
"""
Spotify Playlist Track Extractor & Downloader

This script extracts all track URLs from a given Spotify playlist using the Spotify Web API
and optionally downloads them as MP3 files using spotDL. It uses the Client Credentials flow 
for authentication and handles pagination to retrieve all tracks.

Usage:
    python spotify_playlist_extractor.py <playlist_url>
    python spotify_playlist_extractor.py <playlist_url> --download
    python spotify_playlist_extractor.py <playlist_url> --download --output-dir ~/Music/DJ

Examples:
    # Extract URLs only
    python spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
    
    # Extract URLs and download MP3s
    python spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download
    
    # Download with custom output directory and skip existing files
    python spotify_playlist_extractor.py "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download --output-dir ~/Music --overwrite skip

The script will output all track URLs and optionally download them as MP3 files with metadata.
"""

import os
import sys
import re
import json
import base64
import argparse
import subprocess
import shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import requests
from typing import List, Dict, Optional, Tuple


class SpotifyPlaylistExtractor:
    """Extracts track URLs from Spotify playlists using the Web API."""
    
    def __init__(self, client_id: str, client_secret: str):
        """Initialize with Spotify API credentials."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token: Optional[str] = None
        self.base_url = "https://api.spotify.com/v1"
        
    def authenticate(self) -> bool:
        """
        Authenticate using Client Credentials flow.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        # Prepare the authorization header
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode("ascii")
        auth_base64 = base64.b64encode(auth_bytes).decode("ascii")
        
        # Request token
        url = "https://accounts.spotify.com/api/token"
        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        
        try:
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            token_info = response.json()
            self.access_token = token_info.get("access_token")
            
            if self.access_token:
                print("✓ Successfully authenticated with Spotify API", file=sys.stderr)
                return True
            else:
                print("✗ Failed to get access token", file=sys.stderr)
                return False
                
        except requests.RequestException as e:
            print(f"✗ Authentication failed: {e}", file=sys.stderr)
            return False
    
    def extract_playlist_id(self, playlist_url: str) -> Optional[str]:
        """
        Extract playlist ID from Spotify URL.
        
        Args:
            playlist_url: Spotify playlist URL
            
        Returns:
            str: Playlist ID if found, None otherwise
        """
        # Handle different Spotify URL formats
        patterns = [
            r"spotify:playlist:([a-zA-Z0-9]+)",  # Spotify URI format
            r"open\.spotify\.com/playlist/([a-zA-Z0-9]+)",  # Web URL format
            r"spotify\.com/playlist/([a-zA-Z0-9]+)",  # Alternative web format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, playlist_url)
            if match:
                return match.group(1)
        
        # If it's just an ID
        if re.match(r"^[a-zA-Z0-9]+$", playlist_url):
            return playlist_url
            
        return None
    
    def get_playlist_tracks(self, playlist_id: str) -> List[Dict]:
        """
        Get all tracks from a playlist using pagination.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            List[Dict]: List of track objects
        """
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        all_tracks = []
        url = f"{self.base_url}/playlists/{playlist_id}/tracks"
        
        # Parameters for the request
        params = {
            "fields": "items(track(external_urls,name,artists(name),id,uri,href)),next,total",
            "limit": 100,  # Maximum allowed
            "offset": 0
        }
        
        total_tracks = None
        
        while url:
            try:
                response = requests.get(url, headers=headers, params=params if url == f"{self.base_url}/playlists/{playlist_id}/tracks" else None)
                response.raise_for_status()
                
                data = response.json()
                
                if total_tracks is None:
                    total_tracks = data.get("total", 0)
                    print(f"Found {total_tracks} tracks in playlist", file=sys.stderr)
                
                # Extract tracks from this page
                items = data.get("items", [])
                for item in items:
                    track = item.get("track")
                    if track and track.get("id"):  # Skip null/deleted tracks
                        all_tracks.append(track)
                
                # Check for next page
                url = data.get("next")
                params = None  # For subsequent requests, params are included in the URL
                
                print(f"Retrieved {len(all_tracks)}/{total_tracks} tracks...", file=sys.stderr)
                
            except requests.RequestException as e:
                print(f"✗ Error fetching tracks: {e}", file=sys.stderr)
                break
        
        print(f"✓ Retrieved {len(all_tracks)} tracks total", file=sys.stderr)
        return all_tracks
    
    def extract_track_urls(self, tracks: List[Dict]) -> List[str]:
        """
        Extract Spotify URLs from track objects.
        
        Args:
            tracks: List of track objects from Spotify API
            
        Returns:
            List[str]: List of Spotify track URLs
        """
        urls = []
        
        for track in tracks:
            # Get the external Spotify URL
            external_urls = track.get("external_urls", {})
            spotify_url = external_urls.get("spotify")
            
            if spotify_url:
                urls.append(spotify_url)
            else:
                # Fallback: construct URL from track ID if available
                track_id = track.get("id")
                if track_id:
                    fallback_url = f"https://open.spotify.com/track/{track_id}"
                    urls.append(fallback_url)
                    print(f"Warning: Using fallback URL for track: {track.get('name', 'Unknown')}", file=sys.stderr)
        
        return urls
    
    def get_playlist_info(self, playlist_id: str) -> Optional[Dict]:
        """
        Get basic playlist information.
        
        Args:
            playlist_id: Spotify playlist ID
            
        Returns:
            Dict: Playlist information
        """
        if not self.access_token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/playlists/{playlist_id}"
        params = {
            "fields": "name,description,owner(display_name),tracks(total),external_urls"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"✗ Error fetching playlist info: {e}", file=sys.stderr)
            return None


class SpotDLDownloader:
    """Handles MP3 downloads using spotDL."""
    
    def __init__(self, output_dir: str = ".", overwrite: str = "skip", quality: str = "best"):
        """
        Initialize SpotDL downloader.
        
        Args:
            output_dir: Directory to save downloaded files
            overwrite: How to handle existing files ('skip', 'force', 'prompt')
            quality: Audio quality ('best', 'worst')
        """
        self.output_dir = Path(output_dir).expanduser().resolve()
        self.overwrite = overwrite
        self.quality = quality
        
        # Check if spotdl is available
        if not self._check_spotdl_available():
            raise RuntimeError("spotDL is not available. Please install it with: pip install spotdl")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Download directory: {self.output_dir}", file=sys.stderr)
        
        # Count existing MP3 files
        existing_files = list(self.output_dir.glob("*.mp3"))
        if existing_files:
            print(f"ℹ️  Found {len(existing_files)} existing MP3 files in output directory", file=sys.stderr)
            if self.overwrite == "skip":
                print("ℹ️  Existing files will be skipped automatically", file=sys.stderr)
    
    def _check_spotdl_available(self) -> bool:
        """Check if spotdl command is available."""
        try:
            result = subprocess.run(
                ["spotdl", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Try python module approach
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "spotdl", "--version"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return False
    
    def download_tracks(self, track_urls: List[str], progress_callback=None, timeout_seconds: int = 20) -> Tuple[List[str], List[str]]:
        """
        Download tracks using spotDL with timeout protection.
        
        Args:
            track_urls: List of Spotify track URLs
            progress_callback: Optional callback function for progress updates
            timeout_seconds: Maximum time to wait for each individual track download
            
        Returns:
            Tuple[List[str], List[str]]: (successful_downloads, failed_downloads)
        """
        if not track_urls:
            print("No tracks to download", file=sys.stderr)
            return [], []
        
        print(f"Starting download of {len(track_urls)} tracks (timeout: {timeout_seconds}s per track)...", file=sys.stderr)
        
        # Prepare simple spotdl command
        base_cmd = ["spotdl", "download"]
        
        successful_downloads = []
        failed_downloads = []
        
        # Download tracks one by one to enable per-track timeout
        for i, track_url in enumerate(track_urls, 1):
            print(f"Downloading track {i}/{len(track_urls)}: {track_url}", file=sys.stderr)
            
            # Create command for this specific track - URL must come at the end
            track_cmd = base_cmd + [track_url]
            
            try:
                # Run spotdl command with timeout
                process = subprocess.Popen(
                    track_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(self.output_dir)  # Set working directory to output directory
                )
                
                try:
                    # Wait for process to complete with timeout
                    stdout, _ = process.communicate(timeout=timeout_seconds)
                    
                    if process.returncode == 0:
                        successful_downloads.append(track_url)
                        print(f"  ✓ Track {i} downloaded successfully", file=sys.stderr)
                        
                        # Show relevant output lines
                        for line in stdout.splitlines():
                            line = line.strip()
                            if any(keyword in line.lower() for keyword in ['saved', 'converting', 'found', 'skipping']):
                                print(f"    {line}", file=sys.stderr)
                    else:
                        failed_downloads.append(track_url)
                        print(f"  ✗ Track {i} failed (exit code: {process.returncode})", file=sys.stderr)
                        
                        # Show error output
                        for line in stdout.splitlines():
                            line = line.strip()
                            if any(keyword in line.lower() for keyword in ['error', 'failed', 'not found', 'skipping']):
                                print(f"    {line}", file=sys.stderr)
                                
                except subprocess.TimeoutExpired:
                    # Kill the process if it times out
                    process.kill()
                    process.wait()
                    failed_downloads.append(track_url)
                    print(f"  ⏰ Track {i} timed out after {timeout_seconds} seconds - skipping", file=sys.stderr)
                    
            except Exception as e:
                print(f"  ✗ Error downloading track {i}: {e}", file=sys.stderr)
                failed_downloads.append(track_url)
            
            # Call progress callback
            if progress_callback:
                progress_callback(len(successful_downloads) + len(failed_downloads), len(track_urls))
        
        return successful_downloads, failed_downloads
    
    def download_single_track(self, track_url: str) -> bool:
        """
        Download a single track.
        
        Args:
            track_url: Spotify track URL
            
        Returns:
            bool: True if successful, False otherwise
        """
        successful, failed = self.download_tracks([track_url])
        return len(successful) > 0


def load_credentials_from_env(env_file: str = ".env") -> tuple[str, str]:
    """
    Load Spotify credentials from environment file.
    
    Args:
        env_file: Path to .env file
        
    Returns:
        tuple: (client_id, client_secret)
    """
    # First try to load from .env file in the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, env_file)
    
    client_id = None
    client_secret = None
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        if key in ['SPOTIFY_CLIENT_ID', 'SPOTIFY-CLIENT-ID']:
                            client_id = value
                        elif key in ['SPOTIFY_CLIENT_SECRET', 'SPOTIFY-CLIENT-SECRET']:
                            client_secret = value
    
    # Fallback to environment variables
    if not client_id:
        client_id = os.environ.get('SPOTIFY_CLIENT_ID') or os.environ.get('SPOTIFY-CLIENT-ID')
    if not client_secret:
        client_secret = os.environ.get('SPOTIFY_CLIENT_SECRET') or os.environ.get('SPOTIFY-CLIENT-SECRET')
    
    if not client_id or not client_secret:
        raise ValueError(
            "Spotify credentials not found. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET "
            "in your .env file or environment variables."
        )
    
    return client_id, client_secret


def main():
    """Main function to run the playlist extractor and downloader."""
    parser = argparse.ArgumentParser(
        description="Extract track URLs from a Spotify playlist and optionally download them",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract URLs only
  %(prog)s "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"
  
  # Extract and download MP3s
  %(prog)s "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download
  
  # Download with custom settings
  %(prog)s "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M" --download --output-dir ~/Music/DJ --overwrite skip --quality best
        """
    )
    parser.add_argument(
        "playlist_url",
        help="Spotify playlist URL, URI, or ID"
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show playlist information before extracting URLs"
    )
    parser.add_argument(
        "--format",
        choices=["urls", "json", "csv"],
        default="urls",
        help="Output format for URL extraction (default: urls)"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download MP3 files using spotDL (requires spotDL to be installed)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory to save downloaded MP3 files (default: parent directory of script location)"
    )
    parser.add_argument(
        "--overwrite",
        choices=["skip", "force", "prompt"],
        default="skip",
        help="How to handle existing files (default: skip)"
    )
    parser.add_argument(
        "--quality",
        choices=["best", "worst"],
        default="best",
        help="Audio quality for downloads (default: best)"
    )
    parser.add_argument(
        "--urls-only",
        action="store_true",
        help="Only extract URLs, don't download (useful for testing)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Timeout in seconds for each individual track download (default: 20)"
    )
    
    args = parser.parse_args()
    
    try:
        # Load credentials
        client_id, client_secret = load_credentials_from_env()
        
        # Initialize extractor
        extractor = SpotifyPlaylistExtractor(client_id, client_secret)
        
        # Authenticate
        if not extractor.authenticate():
            sys.exit(1)
        
        # Extract playlist ID
        playlist_id = extractor.extract_playlist_id(args.playlist_url)
        if not playlist_id:
            print(f"✗ Could not extract playlist ID from: {args.playlist_url}", file=sys.stderr)
            sys.exit(1)
        
        print(f"Playlist ID: {playlist_id}", file=sys.stderr)
        
        # Get playlist info if requested
        if args.info:
            info = extractor.get_playlist_info(playlist_id)
            if info:
                print(f"Playlist: {info.get('name', 'Unknown')}", file=sys.stderr)
                print(f"Owner: {info.get('owner', {}).get('display_name', 'Unknown')}", file=sys.stderr)
                print(f"Total tracks: {info.get('tracks', {}).get('total', 'Unknown')}", file=sys.stderr)
                if info.get('description'):
                    print(f"Description: {info['description']}", file=sys.stderr)
                print("", file=sys.stderr)
        
        # Get tracks
        tracks = extractor.get_playlist_tracks(playlist_id)
        
        if not tracks:
            print("No tracks found in playlist", file=sys.stderr)
            sys.exit(1)
        
        # Extract URLs
        urls = extractor.extract_track_urls(tracks)
        
        # Output results (only if not downloading or if urls-only is specified)
        if not args.download or args.urls_only:
            if args.format == "urls":
                for url in urls:
                    print(url)
            elif args.format == "json":
                output = {
                    "playlist_id": playlist_id,
                    "total_tracks": len(tracks),
                    "tracks": [
                        {
                            "name": track.get("name"),
                            "artists": [artist.get("name") for artist in track.get("artists", [])],
                            "url": track.get("external_urls", {}).get("spotify"),
                            "id": track.get("id"),
                            "uri": track.get("uri")
                        }
                        for track in tracks
                    ]
                }
                print(json.dumps(output, indent=2))
            elif args.format == "csv":
                print("name,artists,url,id,uri")
                for track in tracks:
                    name = track.get("name", "").replace('"', '""')
                    artists = "; ".join([artist.get("name", "") for artist in track.get("artists", [])])
                    url = track.get("external_urls", {}).get("spotify", "")
                    track_id = track.get("id", "")
                    uri = track.get("uri", "")
                    print(f'"{name}","{artists}","{url}","{track_id}","{uri}"')
        
        # Download MP3s if requested
        if args.download and not args.urls_only:
            print("\n" + "="*50, file=sys.stderr)
            print("Starting MP3 download process...", file=sys.stderr)
            print("="*50, file=sys.stderr)
            
            # Set default output directory to parent of script directory if not specified
            if args.output_dir is None:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                default_output_dir = os.path.dirname(script_dir)  # Parent directory
                output_dir = default_output_dir
            else:
                output_dir = args.output_dir
            
            try:
                downloader = SpotDLDownloader(
                    output_dir=output_dir,
                    overwrite=args.overwrite,
                    quality=args.quality
                )
                
                def progress_callback(completed: int, total: int):
                    percent = (completed / total) * 100
                    print(f"Progress: {completed}/{total} ({percent:.1f}%)", file=sys.stderr)
                
                successful, failed = downloader.download_tracks(urls, progress_callback, timeout_seconds=args.timeout)
                
                print("\n" + "="*50, file=sys.stderr)
                print("Download Summary:", file=sys.stderr)
                print(f"✓ Successfully downloaded: {len(successful)} tracks", file=sys.stderr)
                if failed:
                    print(f"✗ Failed downloads: {len(failed)} tracks", file=sys.stderr)
                print(f"📁 Files saved to: {downloader.output_dir}", file=sys.stderr)
                print("="*50, file=sys.stderr)
                
            except RuntimeError as e:
                print(f"✗ Download error: {e}", file=sys.stderr)
                print("To install spotDL: pip install spotdl", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"✓ Successfully extracted {len(urls)} track URLs", file=sys.stderr)
        
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
