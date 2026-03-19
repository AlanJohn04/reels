import argparse
import os
import requests
import sys

def download_images(chapter_num, image_urls, output_base_dir):
    chapter_dir = os.path.join(output_base_dir, f"chapter_{str(chapter_num).zfill(3)}")
    os.makedirs(chapter_dir, exist_ok=True)
    
    print(f"Downloading {len(image_urls)} images to {chapter_dir}...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://manganato.com/"
    }
    
    for i, url in enumerate(image_urls):
        try:
            filename = f"page_{str(i+1).zfill(3)}.jpg"
            filepath = os.path.join(chapter_dir, filename)
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(filepath, "wb") as f:
                f.write(response.content)
                
            print(f"  Saved {filename}")
        except Exception as e:
            print(f"  ERROR downloading {url}: {e}")
            
    print("Download complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--urls", required=True, help="Comma-separated image URLs")
    parser.add_argument("--output-dir", required=True)
    
    args = parser.parse_args()
    url_list = args.urls.split(',')
    download_images(args.chapter, url_list, args.output_dir)
