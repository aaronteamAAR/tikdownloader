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
DOWNLOAD_LIMIT = 60
SCROLL_COUNT = 10
OUTPUT_DIR = "ig_downloads_fixed"
COOKIE_FILE = os.path.join(os.getcwd(), 'cookies.txt')

def check_setup():
    if not os.path.exists(COOKIE_FILE):
        print("[ERROR] cookies.txt is missing! Instagram will block these requests.")
        sys.exit(1)

def run_yt_dlp(url, index):
    """
    High-quality Instagram download using bestvideo+bestaudio.
    Forces Instagram extractor and sorts by best resolution, bitrate, and fps.
    """
    output_template = os.path.join(OUTPUT_DIR, f"reel_{index}_%(id)s.%(ext)s")
    
    cmd = [
    'yt-dlp',
    '--cookies', COOKIE_FILE,
    '--ies', 'instagram',
    '-f', 'bv*+ba/best',
    '--format-sort', 'res,br,fps',
    '--merge-output-format', 'mp4',
    '-o', output_template,
    '--no-playlist',
    url
    ]


    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   [SUCCESS] Downloaded: {url}")
            return True
        else:
            print(f"   [FAILED] yt-dlp Error: {result.stderr[:150]}...")
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
    time.sleep(7)

    found_links = set()

    for i in range(SCROLL_COUNT):
        # 🔥 Use JS to extract hrefs directly (no stale elements)
        links = driver.execute_script("""
            return Array.from(document.querySelectorAll("a[href*='/reel/'], a[href*='/p/']"))
                .map(a => a.href);
        """)

        for href in links:
            if href:
                clean_url = href.split('?')[0].rstrip('/')
                found_links.add(clean_url)

        print(f"   Scroll {i+1}: Found {len(found_links)} unique items")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

    driver.quit()
    return list(found_links)

def main():
    check_setup()
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    target = input("Enter IG Profile URL: ").strip()
    links = scrape_clean_links(target)
    
    if not links:
        print("No links found. Please check if your browser window shows a 'Login' wall.")
        return

    print(f"\nSTEP 2: Starting High-Quality Downloads...")
    count = 0
    for i, link in enumerate(links):
        if count >= DOWNLOAD_LIMIT:
            break
        if run_yt_dlp(link, count + 1):
            count += 1

    print(f"\nFINISHED: {count} videos saved to '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()
