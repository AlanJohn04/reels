# REELS LABS — Manhwa AI Automation Engine

A high-performance processing pipeline for automating Manhwa/Manga reels for YouTube Shorts.

## 🚀 Tech Stack
- **Frontend**: Glassmorphism UI (HTML/CSS/JS)
- **Backend**: Python Flask (Thread-based Task Queue)
- **Production**: MoviePy (FFMPEG), edge-tts
- **API**: YouTube Data API v3

## 🛠️ Hosting on Oracle Cloud (Always Free)
This project requires significant CPU (for video rendering) and RAM. We recommend the **Oracle Cloud Ampere A1** instance (4 OCPUs, 24GB RAM).

### 1. VM Configuration
- **Shape**: `VM.Standard.A1.Flex`
- **OS**: Ubuntu 22.04 LTS
- **Networking**: Allow Ingress on port `5000` (TCP) in Security Lists.

### 2. Deployment Commands
Once inside your VM terminal:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3-pip ffmpeg -y

# Clone your repository
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME

# Install Python packages
pip install -r requirements.txt

# Manually upload your secrets (NOT recommended for GitHub)
# Use SCP or FTP to move 'client_secrets.json' and 'youtube_token.json' to the root folder.
```

### 3. Run the Server
```bash
python3 server.py
```
Access via `http://YOUR_VM_IP:5000`.

## ☁️ Hosting on Render.com
Render is a great free alternative. Follow these steps:

1.  **Connect your GitHub Repository** to a new **Web Service** on Render.
2.  **Runtime**: Python
3.  **Build Command**: `pip install -r requirements.txt`
4.  **Start Command**: `python server.py`
5.  **Environment Variables (CRITICAL)**:
    Since Render doesn't support persistent local JSON files on the free tier, you must provide your secrets as environment variables:
    *   `YOUTUBE_TOKEN_JSON`: Paste the entire content of `youtube_token.json` into this value.
    *   `YOUTUBE_CLIENT_SECRETS_JSON`: Paste the entire content of `client_secrets.json` into this value.
    *(You can find these files in your local project folder)*.

**Note for Free Tier Users**: 
- **Video Rendering** is CPU-intensive. On the free tier, it may take 20-30 minutes and might occasionally time out or run out of memory (512MB). If this happens, consider a **Starter** or **Pro** plan on Render, or use **Oracle Cloud's Always Free** tier which provides 24GB RAM and 4 CPUs for free.

## 📂 Project Structure
- `server.py`: Flask web server and task manager (Background processing).
- `process_chapter.py`: Orchestrates scraping, audio, and rendering.
- `render.py`: MoviePy engine (v2.0) with beat-synced visuals.
- `upload.py`: YouTube API integration with environment variable support.
- `local_tts.py`: edge-tts voice generation (Synced to VTT).

## ⚠️ Security Warning
**NEVER** commit `client_secrets.json` or `youtube_token.json` to your public GitHub repository. Use the Environment Variables method on Render to keep them secure.
