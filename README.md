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

## 📂 Project Structure
- `server.py`: Flask web server and task manager.
- `process_chapter.py`: Orchestrates scraping, audio, and rendering.
- `render.py`: MoviePy engine for beat-synced visuals.
- `upload.py`: YouTube API integration.
- `local_tts.py`: edge-tts voice generation.

## ⚠️ Security Warning
**NEVER** commit `client_secrets.json` or `youtube_token.json` to a public GitHub repository. They are ignored by `.gitignore` in this project.
