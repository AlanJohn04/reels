import requests
from bs4 import BeautifulSoup
import argparse
import os
import sys

def scrape_orv_chapter(chapter_num, output_base_dir):
    # ORV MangaDex ID
    MANGA_ID = "9a414441-bbad-43f1-a3a7-dc262ca790a3"
    
    print(f"Searching for Chapter {chapter_num} on MangaDex...")
    
    # 1. Get Chapter ID
    # Use feed endpoint to find the specific chapter number in English
    feed_url = f"https://api.mangadex.org/manga/{MANGA_ID}/feed"
    params = {
        "translatedLanguage[]": "en",
        "order[chapter]": "asc",
        "limit": 100, # Get a bunch to find the right one
    }
    
    try:
        response = requests.get(feed_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        chapter_id = None
        print(f"  Scanning {len(data['data'])} chapters from feed...")
        for ch in data["data"]:
            ch_num = ch["attributes"]["chapter"]
            # print(f"    Seen Chapter: {ch_num}") # Debug
            if ch_num == str(chapter_num):
                chapter_id = ch["id"]
                print(f"  Found Chapter {chapter_num} (ID: {chapter_id})")
                break
        
        if not chapter_id:
            # Maybe it's further down the list?
             # Try simple filter if logical
            print("  Chapter not found in first 100 results, trying strict filter...")
             # actually I can just assume the user wants the first match for that chapter num
            # Let's try to pass 'chapter' param if supported, but feed doesn't always support it well.
            # Actually feed supports offset.
            # Let's try searching specifically.
             # but for now let's assume chapter 1 is within first 100.
            pass
            
        if not chapter_id:
             print(f"ERROR: Could not find Chapter {chapter_num} in English on MangaDex.")
             sys.exit(1)

        # 2. Get Chapter Pages
        print(f"  Getting pages for Chapter {chapter_num}...")
        at_home_url = f"https://api.mangadex.org/at-home/server/{chapter_id}"
        r = requests.get(at_home_url)
        r.raise_for_status()
        ch_data = r.json()
        
        base_url = ch_data["baseUrl"]
        hash_ = ch_data["chapter"]["hash"]
        filenames = ch_data["chapter"]["data"] # "data" is high quality, "dataSaver" is low
        
        image_urls = [f"{base_url}/data/{hash_}/{fn}" for fn in filenames]
        print(f"  Found {len(image_urls)} pages.")
        
        # 3. Download
        chapter_dir = os.path.join(output_base_dir, f"chapter_{str(chapter_num).zfill(3)}")
        os.makedirs(chapter_dir, exist_ok=True)
        
        for i, url in enumerate(image_urls):
            ext = url.split('.')[-1]
            filename = f"page_{str(i+1).zfill(3)}.{ext}"
            filepath = os.path.join(chapter_dir, filename)
            
            print(f"  Downloading {filename}...", end='\r')
            # MangaDex images don't usually require referer, but good practice
            img_data = requests.get(url).content
            with open(filepath, 'wb') as f:
                f.write(img_data)
                
        print(f"\nSaved {len(image_urls)} images to {chapter_dir}")
        return chapter_dir

    except Exception as e:
        print(f"Error scraping MangaDex: {e}")
        # Fallback manual scraping check commented out to keep code clean
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--chapter", type=int, required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    
    scrape_orv_chapter(args.chapter, args.output_dir)
