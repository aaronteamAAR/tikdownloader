import subprocess
import json
import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException

# --- Configuration ---
DOWNLOAD_LIMIT = 60      # Maximum number of videos to download
SCROLL_COUNT = 4         # Number of times to scroll down the page

# --- Setup ---
OUTPUT_DIR = "facebook_downloads"
COOKIE_FILE = os.path.join(os.getcwd(), 'cookies.txt')

def check_setup():
    """Checks for the existence of critical files and libraries."""
    if not os.path.exists(COOKIE_FILE):
        print("\n" + "="*70)
        print("[CRITICAL SETUP ERROR] 'cookies.txt' is MISSING.")
        print("Facebook downloads REQUIRE a valid login session.")
        print("="*70)
        sys.exit(1)
    
    try:
        import selenium
        import webdriver_manager
        print("[INFO] Dependencies are available.")
    except ImportError:
        print("\n[CRITICAL ERROR] Missing selenium or webdriver-manager. Run: pip install selenium webdriver-manager")
        sys.exit(1)

def run_yt_dlp(url, options, silent=False):
    """Runs yt-dlp as a subprocess."""
    cmd = ['yt-dlp', url] + options
    cmd.extend(['--cookies', COOKIE_FILE])

    max_retries = 3
    base_delay = 5

    for attempt in range(max_retries):
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                encoding='latin-1'
            )
            return process.stdout
        except subprocess.CalledProcessError as e:
            stderr_lower = e.stderr.lower() if e.stderr else ""
            if "login" in stderr_lower or "private" in stderr_lower:
                raise Exception(f"Authentication Failed: {e.stderr}")
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
            else:
                raise Exception(f"yt-dlp failed: {e.stderr}")

def scrape_video_urls_with_selenium(facebook_url):
    """Uses Selenium to extract video links."""
    print("\nSTEP 1: Scraping video links...")
    options = Options()
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")

    try:
        driver_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=driver_service, options=options)
        driver.get(facebook_url)
        time.sleep(60) # Initial wait for content

        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(SCROLL_COUNT):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(7)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height: break
            last_height = new_height

        script = """
            let urls = new Set();
            document.querySelectorAll('a[href*="/videos/"], a[href*="/reel/"]').forEach(a => {
                const url = a.href.split('?')[0];
                if (url.includes('facebook.com')) urls.add(url);
            });
            document.querySelectorAll('div[data-video-id]').forEach(div => {
                const vid = div.getAttribute('data-video-id');
                urls.add(`${window.location.origin}/video.php?v=${vid}`);
            });
            return Array.from(urls);
        """
        urls = driver.execute_script(script)
        driver.quit()
        return urls
    except Exception as e:
        print(f"Scraping error: {e}")
        return []

def get_metadata(video_urls):
    """Step 2: Fetches metadata including descriptions (captions)."""
    print("\nSTEP 2: Fetching metadata and captions...")
    video_entries = []
    options = ['--dump-json']
    
    for i, url in enumerate(video_urls):
        print(f"   -> Processing {i+1}/{len(video_urls)}...", end='\r')
        try:
            stdout = run_yt_dlp(url, options, silent=True)
            data = json.loads(stdout)
            
            # Capture description for the caption file
            video_entries.append({
                'url': data.get('webpage_url'),
                'title': data.get('title', 'Untitled Video'),
                'view_count': data.get('view_count', 0) or 0,
                'description': data.get('description', 'No caption provided.')
            })
        except:
            continue
            
    print(f"\nExtracted metadata for {len(video_entries)} videos.")
    return video_entries

def filter_and_sort(video_entries):
    """Step 3: Sorts by popularity."""
    sorted_videos = sorted(video_entries, key=lambda x: x['view_count'], reverse=True)
    return sorted_videos[:DOWNLOAD_LIMIT]

def download_videos(final_list):
    """Step 4: Downloads videos and saves captions to .txt files."""
    print("\n" + "="*60)
    print(f"STEP 4: Downloading {len(final_list)} videos and saving captions...")
    print("="*60)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for i, video in enumerate(final_list):
        index_str = f"{i+1:02d}"
        print(f"\n[{index_str}/{len(final_list)}] Processing: {video['title'][:40]}...")

        # 1. Save the Caption to a Text File
        # We use a clean filename that matches the video prefix
        txt_filename = f"viral_{index_str}_caption.txt"
        txt_path = os.path.join(OUTPUT_DIR, txt_filename)
        
        try:
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"VIDEO TITLE: {video['title']}\n")
                f.write(f"SOURCE URL: {video['url']}\n")
                f.write(f"VIEWS: {video['view_count']:,}\n")
                f.write("-" * 30 + "\n")
                f.write(f"CAPTION:\n{video['description']}")
            print(f"    -> Caption saved: {txt_filename}")
        except Exception as e:
            print(f"    -> WARNING: Could not save caption: {e}")

        # 2. Download the Video
        output_template = os.path.join(OUTPUT_DIR, f"viral_{index_str}_%(title)s.%(ext)s")
        options = [
            '-o', output_template,
            '-f', 'bestvideo*+bestaudio/best',
            '--recode-video', 'mp4',
        ]
        
        try:
            run_yt_dlp(video['url'], options, silent=True)
            print(f"    -> Video download complete.")
        except Exception as e:
            print(f"    -> WARNING: Failed to download video: {e}")

def main():
    check_setup()
    facebook_url = input("Enter Facebook Page URL: ").strip()
    if not facebook_url: return

    if "web.facebook.com" in facebook_url:
        facebook_url = facebook_url.replace("web.facebook.com", "www.facebook.com")

    try:
        all_urls = scrape_video_urls_with_selenium(facebook_url)
        if not all_urls: return
        
        all_videos = get_metadata(all_urls)
        viral_videos = filter_and_sort(all_videos)
        download_videos(viral_videos)
        
        print(f"\n\nPROCESS COMPLETE. Check '{OUTPUT_DIR}' for files.")
    except Exception as e:
        print(f"\n[PROGRAM ERROR]: {e}")

if __name__ == "__main__":
    main()