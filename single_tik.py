import subprocess
import os

# --- Configuration ---
OUTPUT_DIR = "single_downloads"
COOKIE_FILE = os.path.join(os.getcwd(), 'cookies.txt')
# ---------------------

def run_yt_dlp(url, options):
    """
    Runs yt-dlp with impersonation to bypass TikTok blocks.
    """
    # Using 'chrome' impersonation to avoid extraction errors
    cmd = ['yt-dlp', '--impersonate', 'chrome', url] + options
    
    if os.path.exists(COOKIE_FILE):
        cmd.extend(['--cookies', COOKIE_FILE])

    try:
        process = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True, 
            encoding='utf-8'
        )
        return process.stdout
    except subprocess.CalledProcessError as e:
        raise Exception(f"yt-dlp failed: {e.stderr}")

def download_single_video(url):
    """
    Downloads a single video URL.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"\nTarget URL: {url}")
    print("Attempting to download...")

    # Simple template for single files
    output_template = os.path.join(OUTPUT_DIR, "%(title)s_%(id)s.%(ext)s")

    options = [
        '-o', output_template,
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        '--no-playlist' # Ensures it only grabs the video even if it's part of a set
    ]

    try:
        run_yt_dlp(url, options)
        print("Done! Check the 'single_downloads' folder.")
    except Exception as e:
        print(f"\n[ERROR] Failed to download: {e}")

def main():
    print("--- TikTok Single Video Downloader ---")
    video_url = input("Paste the TikTok video URL: ").strip()
    
    if not video_url:
        print("URL cannot be empty.")
        return

    download_single_video(video_url)

if __name__ == "__main__":
    main()