import os
import sys
import requests
import argparse
import subprocess
import shutil
import glob
from bs4 import BeautifulSoup
from PIL import Image
def get_chapter_dir(chapter):
    return os.path.join("chapters", f"chapter_{str(chapter).zfill(3)}")

import re

def scrape_images(chapter, series="Omniscient Reader's Viewpoint"):
    print(f"Attempting to find images for {series} Chapter {chapter}...")
    
    # Construction: Convert series name to URL-friendly slugs
    slug = re.sub(r'\W+', '-', series.lower()).strip('-')
    
    # 1. Try common sources
    sources = [
        # Some custom sites may use series-name.com/chapter-X
        f"https://{slug.replace('-','').strip()}.com/chapter-{chapter}/",
        # Generic sites
        f"https://chapmanganato.to/manga-{slug}/chapter-{chapter}",
        f"https://asuratoon.com/{slug}-chapter-{chapter}/",
        # Legacy ORV if matched
        f"https://w49.omniscientreaderviewpoint.com/manga/omniscient-readers-viewpoint-chapter-{chapter}/" if "omniscient" in series.lower() else ""
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for target_url in filter(None, sources):
        try:
            print(f"  Checking {target_url}...")
            resp = requests.get(target_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                # Regex to find blogger URLs (common in many scans)
                matches = re.findall(r'src="(https?://[^"]+\.(?:jpg|png|webp|jpeg))"', resp.text)
                
                # Filter out small or logo-like things
                unique_images = []
                seen = set()
                for url in matches:
                    if url not in seen and not any(x in url.lower() for x in ['logo', 'icon', 'facebook', 'twitter']):
                        unique_images.append(url)
                        seen.add(url)
                
                if len(unique_images) > 10:
                    print(f"  SUCCESS: Found {len(unique_images)} images.")
                    return unique_images
                
                # Fallback to BeautifulSoup logic if regex fails to find > 10
                soup = BeautifulSoup(resp.text, 'html.parser')
                images = soup.find_all('img')
                candidates = []
                for img in images:
                    src = img.get('src') or img.get('data-src') or img.get('data-original')
                    if src and src.startswith('http') and not any(x in src.lower() for x in ['logo', 'icon', 'facebook', 'twitter']):
                        candidates.append(src)
                
                if len(candidates) > 10:
                    print(f"  SUCCESS: Found {len(candidates)} images via BeautifulSoup.")
                    return candidates
                    
        except Exception as e:
            print(f"  Error checking {target_url}: {e}")

    return None

def download_images(image_urls, output_dir):
    # Check for already existing content
    if os.path.exists(output_dir):
        # Only check images
        files = [f for f in glob.glob(os.path.join(output_dir, "*")) 
                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        
        if files:
            sizes = [os.path.getsize(f) for f in files]
            # If all files are identical size, it's junk
            if len(sizes) > 5 and len(set(sizes)) == 1:
                print("  Cleaning up junk/identical files from previous run...")
                for f in files:
                    os.remove(f)
            elif len(files) > 0:
                 print(f"  Folder {output_dir} has content. Skipping download.")
                 return True

    os.makedirs(output_dir, exist_ok=True)
    print(f"Downloading {len(image_urls)} images to {output_dir}...")
    headers = {"User-Agent": "Mozilla/5.0"}

    count = 0
    for i, url in enumerate(image_urls):
        try:
            ext = url.split('.')[-1].split('?')[0]
            if len(ext) > 4 or not ext: ext = "jpg"
            filename = f"page_{str(count+1).zfill(3)}.{ext}"
            filepath = os.path.join(output_dir, filename)
            
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                with open(filepath, 'wb') as f:
                    f.write(resp.content)
                
                # Check image validity using Pillow
                try:
                    with Image.open(filepath) as img:
                        w, h = img.size
                        if w < 200 or h < 200:
                            print(f"  Skipping small image {w}x{h}", end='\r')
                            os.remove(filepath)
                            continue
                        if img.format == 'GIF':
                             rgb_im = img.convert('RGB')
                             new_filepath = os.path.splitext(filepath)[0] + ".jpg"
                             rgb_im.save(new_filepath)
                             os.remove(filepath)
                             filename = os.path.basename(new_filepath)
                except Exception as e:
                    print(f"  Invalid image: {e}", end='\r')
                    os.remove(filepath)
                    continue

                count += 1
                print(f"  Saved {filename}", end='\r')
        except:
            pass
    
    print(f"\n  Download complete. {count} valid images saved.")
    
    # Post-download validation
    files = glob.glob(os.path.join(output_dir, "*"))
    sizes = [os.path.getsize(f) for f in files if os.path.isfile(f)]
    if len(sizes) > 0 and len(set(sizes)) == 1:
        print("  ERROR: All downloaded files are identical (likely anti-bot block). Deleting...")
        shutil.rmtree(output_dir)
        return False
        
    return count > 0

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, default=1)
    parser.add_argument("--series", type=str, default="Omniscient Reader's Viewpoint")
    parser.add_argument("--script", type=str, default="")
    args = parser.parse_args()

    # Create safe directory and series-based targeting
    safe_series = re.sub(r'\W+', '_', args.series.lower()).strip('_')
    chapter_dir = os.path.join("chapters", f"{safe_series}_ch{str(args.chapter).zfill(3)}")
    os.makedirs(chapter_dir, exist_ok=True)
    
    # 1. Image Acquisition
    success = False
    
    # Search for any provided images in folder
    if os.path.exists(chapter_dir) and any(f.lower().endswith(('.jpg', '.png', '.webp')) for f in os.listdir(chapter_dir)):
        print(f"  Existing images found for {args.series} in {chapter_dir}. Skipping scrape.")
        success = True
    else:
        # Try finding images for this series
        slug = re.sub(r'[^a-zA-Z0-9]', '-', args.series.lower())
        manganato_url = f"https://chapmanganato.to/manga-{slug}/chapter-{args.chapter}"
        asura_url = f"https://asuratoon.com/{slug}-chapter-{args.chapter}/"
        
        # Simple fallback check (very basic)
        urls = scrape_images(args.chapter, series=args.series)
        if urls: success = download_images(urls, chapter_dir)
        
    if not success:
        print(f"\nCould not find images for {args.series}. Providing URL input...")
        # (Could add more interactive logic here if not automate)
    
    # 2. Audio Generation
    audio_path = os.path.join(chapter_dir, "narration.mp3")
    vtt_path = os.path.join(chapter_dir, "narration.vtt")
    
    # If a custom script is provided, use it
    if args.script and os.path.exists(args.script):
        script_path = args.script
    else:
        # Check for specific script_chX.txt in root (legacy) or chapter folder
        script_path = os.path.join(chapter_dir, "script.txt")
        if not os.path.exists(script_path):
             # Try default script in root for ORV if it matches
             if "omniscient" in args.series.lower() and args.chapter == 1:
                 script_path = "script_ch1.txt"
    
    if os.path.exists(script_path):
        if not os.path.exists(audio_path) or not os.path.exists(vtt_path):
            print("\nGenerating Audio & Subtitles...")
            try:
                subprocess.run([sys.executable, "local_tts.py", "--text-file", script_path, "--output-file", audio_path, "--output-vtt", vtt_path], check=True)
            except Exception as e:
                print(f"TTS Failed: {e}")
                sys.exit(1)
    else:
        print(f"ERROR: No script found at {script_path}.")
        sys.exit(1)

    # 3. Video Rendering
    video_path = os.path.join(chapter_dir, "final_reel.mp4")
    print(f"\nRendering {args.series} Video...")
    try:
        subprocess.run([sys.executable, "render.py", 
                        "--chapter", str(args.chapter), 
                        "--chapter-dir", chapter_dir, 
                        "--audio", audio_path, 
                        "--vtt", vtt_path,
                        "--output", video_path,
                        "--min-duration", "15"], check=True)
    except subprocess.CalledProcessError:
        sys.exit(1)

    # 4. Upload
    print(f"\nUploading {args.series} to YouTube...")
    # Remove Emojis from Title for Windows shell safety during subprocess call
    clean_series = re.sub(r'[^\x00-\x7F]+', '', args.series)
    title = f"{clean_series} Chapter {args.chapter} (Full Recap) #Shorts"
    desc = f"Catch the full recap of {args.series} Chapter {args.chapter}. Subscribe for more daily recaps! | #manhwa #recap #shorts #webtoon"
    try:
        res = subprocess.run([sys.executable, "upload.py", 
                        "--video", video_path, 
                        "--title", title, 
                        "--description", desc,
                        "--privacy", "public"], 
                        capture_output=True, text=True, check=True)
        print(res.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Upload failed for {args.series}.")
        print(f"Command Error: {e.stderr}")
        sys.exit(1)

    print("\nSUCCESS! Reel uploaded.")

if __name__ == "__main__":
    main()
