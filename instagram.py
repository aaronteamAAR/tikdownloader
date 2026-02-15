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
SCROLL_COUNT = 6
OUTPUT_DIR = "ig_downloads_fixed"
COOKIE_FILE = os.path.join(os.getcwd(), 'cookies.txt')

def check_setup():
    if not os.path.exists(COOKIE_FILE):
        print("[ERROR] cookies.txt is missing! Instagram will block these requests.")
        sys.exit(1)

def convert_to_mov(mp4_path):
    mov_path = mp4_path.replace(".mp4", ".mov")

    cmd = [
        "ffmpeg",
        "-i", mp4_path,
        "-c", "copy",  # 🔥 No re-encoding (keeps full quality)
        mov_path,
        "-y"
    ]

    try:
        subprocess.run(cmd, capture_output=True)
        os.remove(mp4_path)  # Delete original MP4
        print(f"   [CONVERTED] → {mov_path}")
    except Exception as e:
        print(f"   [ERROR] MOV conversion failed: {e}")

def run_yt_dlp(url, index):
    """
    High-quality Instagram download using bestvideo+bestaudio.
    Automatically converts to MOV after download.
    """
    output_template = os.path.join(OUTPUT_DIR, f"reel_{index}_%(id)s.%(ext)s")
    
    cmd = [
        'yt-dlp',
        '-U',
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

            # Find downloaded MP4 file
            for file in os.listdir(OUTPUT_DIR):
                if file.startswith(f"reel_{index}_") and file.endswith(".mp4"):
                    convert_to_mov(os.path.join(OUTPUT_DIR, file))

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
    time.sleep(5)

    found_links = set()

    for i in range(SCROLL_COUNT):
        elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/reel/') or contains(@href, '/p/')]")
        for e in elements:
            href = e.get_attribute('href')
            if href:
                clean_url = href.split('?')[0]
                if clean_url.endswith('/'):
                    clean_url = clean_url[:-1]
                found_links.add(clean_url)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"   Scroll {i+1}: Found {len(found_links)} unique items")
        time.sleep(15)

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

    print(f"\nSTEP 2: Downloading + Converting to MOV...")
    count = 0
    for i, link in enumerate(links):
        if count >= DOWNLOAD_LIMIT:
            break
        if run_yt_dlp(link, count + 1):
            count += 1

    print(f"\nFINISHED: {count} videos saved as MOV in '{OUTPUT_DIR}'")

if __name__ == "__main__":
    main()
