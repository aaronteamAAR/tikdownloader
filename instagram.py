import subprocess
import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# --- Configuration ---
DOWNLOAD_LIMIT = 40
SCROLL_COUNT = 6
OUTPUT_DIR = "ig_downloads_fixed"
COOKIE_FILE = os.path.join(os.getcwd(), 'cookies.txt')

def check_setup():
    if not os.path.exists(COOKIE_FILE):
        print("[ERROR] cookies.txt is missing! Instagram will block these requests.")
        sys.exit(1)

def run_yt_dlp(url, index):
    """
    Directly targets the Instagram extractor.
    Using --ies instagram ensures it doesn't fall back to 'generic'.
    """
    output_template = os.path.join(OUTPUT_DIR, f"reel_{index}_%(id)s.%(ext)s")
    
    cmd = [
        'yt-dlp',
        '--cookies', COOKIE_FILE,
        '--ies', 'instagram',  # Force Instagram extractor
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '--merge-output-format', 'mp4',
        '--format-sort', 'res,br,fps', # Sort by Resolution, then Bitrate, then FPS
        '-o', output_template,
        '--no-playlist',
        url
    ]

    try:
        # We use 'capture_output' to keep the terminal clean
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   [SUCCESS] Downloaded: {url}")
            return True
        else:
            print(f"   [FAILED] yt-dlp Error: {result.stderr[:100]}...")
            return False
    except Exception as e:
        print(f"   [ERROR] Runtime error: {e}")
        return False

def scrape_clean_links(profile_url):
    print(f"\nSTEP 1: Scraping and Cleaning Links...")
    options = Options()
    options.add_argument("--window-size=1200,800")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(profile_url)
    time.sleep(5) 

    found_links = set()
    
    for i in range(SCROLL_COUNT):
        # We look for any 'a' tag that contains 'reel' or 'p' in the href
        elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/reel/') or contains(@href, '/p/')]")
        for e in elements:
            href = e.get_attribute('href')
            if href:
                # IMPORTANT: Clean the URL to the base ID
                # Example: https://www.instagram.com/reels/C4xABC123/
                clean_url = href.split('?')[0]
                if clean_url.endswith('/'): clean_url = clean_url[:-1]
                found_links.add(clean_url)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"   Scroll {i+1}: Found {len(found_links)} unique items")
        time.sleep(15)

    driver.quit()
    return list(found_links)

def main():
    check_setup()
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    target = input("Enter IG Profile URL: ").strip()
    links = scrape_clean_links(target)
    
    if not links:
        print("No links found. Please check if your browser window shows a 'Login' wall.")
        return

    print(f"\nSTEP 2: Starting High-Quality Downloads...")
    count = 0
    for i, link in enumerate(links):
        if count >= DOWNLOAD_LIMIT: break
        if run_yt_dlp(link, count + 1):
            count += 1

    print(f"\nFINISHED: {count} videos saved to '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()