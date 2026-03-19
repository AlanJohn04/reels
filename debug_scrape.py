import requests

url = "https://chapmanganato.to/manga-bf978762/chapter-1"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://manganato.com/"
}

try:
    print(f"Fetching {url}...")
    resp = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"URL: {resp.url}")
    print("Content preview (first 1000 chars):")
    print(resp.text[:1000])
    
    if "container-chapter-reader" in resp.text:
        print("\nFound 'container-chapter-reader'!")
    else:
        print("\n'container-chapter-reader' NOT found.")
        
except Exception as e:
    print(f"Error: {e}")
