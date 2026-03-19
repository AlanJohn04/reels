#!/usr/bin/env python3
"""
ORV YouTube Automation - YouTube Uploader
Uses YouTube Data API v3 with OAuth2
Dependencies: google-auth, google-auth-oauthlib, google-api-python-client
Install: pip install google-auth google-auth-oauthlib google-api-python-client
"""

import argparse
import json
import os
import sys
import time
import random
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from googleapiclient.errors import HttpError
except ImportError:
    print("ERROR: Missing Google API libraries.")
    print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)


# ── Configuration ─────────────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
# Get the directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CREDENTIALS_FILE = os.path.join(BASE_DIR, "client_secrets.json")
TOKEN_FILE = os.path.join(BASE_DIR, "youtube_token.json")

# Retry configuration for network issues
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds


STATE_FILE = os.path.join(BASE_DIR, "orv_state.json")

def get_youtube_service():
    """Authenticate and return YouTube API service."""
    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            print(f"  Token load failed: {e}, will re-authenticate")
            creds = None

    # Refresh or re-authenticate if needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("  Refreshing access token...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"  Token refresh failed: {e}")
                creds = None

        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                print(f"\nERROR: Client secrets file not found: {CREDENTIALS_FILE}")
                print("Download it from Google Cloud Console > APIs > Credentials")
                sys.exit(1)

            print("  Opening OAuth2 flow (first time setup)...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Use local server flow for Windows/Desktop with FIXED port
            creds = flow.run_local_server(port=8080)

        # Save credentials for next run
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
        print("  Credentials saved")

    return build("youtube", "v3", credentials=creds)


def upload_video(
    video_path: str,
    title: str,
    description: str,
    tags: str,
    category_id: str = "24",
    privacy: str = "public"
):
    """Upload video to YouTube with retry logic."""

    if not os.path.exists(video_path):
        print(f"ERROR: Video file not found: {video_path}")
        sys.exit(1)

    file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"  YouTube Uploader — ORV Automation")
    print(f"{'='*60}")
    print(f"  File: {video_path}")
    print(f"  Size: {file_size_mb:.1f} MB")
    print(f"  Title: {title}")
    print(f"  Privacy: {privacy}")
    print()

    # Build metadata
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tag_list,
            "categoryId": category_id,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    # Set up resumable upload
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=50 * 1024 * 1024  # 50MB chunks
    )

    youtube = get_youtube_service()

    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  Starting upload (attempt {attempt}/{MAX_RETRIES})...")
            request = youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )

            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    bar = "#" * (progress // 5) + "-" * (20 - progress // 5)
                    print(f"\r  Uploading: [{bar}] {progress}%", end="", flush=True)

            print(f"\n  Upload complete!")
            video_id = response.get("id")
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            print(f"  Video ID: {video_id}")
            print(f"  URL: {video_url}")
            print(f"SUCCESS:{video_id}")  # Parsed by n8n
            return video_id

        except HttpError as e:
            error_reason = json.loads(e.content).get("error", {}).get("errors", [{}])[0].get("reason", "unknown")

            if e.resp.status in [500, 502, 503, 504]:
                # Retryable server errors
                wait_time = RETRY_DELAY * (2 ** (attempt - 1))  # Exponential backoff
                print(f"\n  Server error ({e.resp.status}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

            elif error_reason == "quotaExceeded":
                print(f"\n  YouTube API quota exceeded! (10,000 units/day limit)")
                print("  Upload postponed until tomorrow.")
                sys.exit(2)  # Special exit code for quota errors

            elif e.resp.status == 403:
                print(f"\n  ERROR: Access denied. Check YouTube channel is set up properly.")
                sys.exit(1)

            else:
                print(f"\n  YouTube API error: {e}")
                sys.exit(1)

        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"\n  Upload failed: {e}. Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print(f"\n  ERROR: Upload failed after {MAX_RETRIES} attempts: {e}")
                sys.exit(1)

    print(f"ERROR: Upload failed after {MAX_RETRIES} attempts")
    sys.exit(1)


# ── CLI Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", required=True, help="Path to MP4 file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", required=True, help="Video description")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--category", default="24", help="YouTube category ID")
    parser.add_argument("--privacy", default="public",
                        choices=["public", "unlisted", "private"],
                        help="Privacy status")

    args = parser.parse_args()

    upload_video(
        video_path=args.video,
        title=args.title,
        description=args.description,
        tags=args.tags,
        category_id=args.category,
        privacy=args.privacy
    )