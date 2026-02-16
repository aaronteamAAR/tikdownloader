import subprocess
import os
import sys

# --- Configuration ---
INPUT_FILE = "links.txt"
OUTPUT_DIR = "laundry_instagram"
COOKIE_FILE = os.path.join(os.getcwd(), 'cookies.txt')

def check_setup():
    """Validates that necessary files and folders exist."""
    if not os.path.exists(COOKIE_FILE):
        print(f"[WARNING] {COOKIE_FILE} not found. Private content may not download.")
    
    if not os.path.exists(INPUT_FILE):
        print(f"[ERROR] {INPUT_FILE} is missing! Please create it and add your links.")
        sys.exit(1)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"[INFO] Created directory: {OUTPUT_DIR}")

def run_yt_dlp(url, index):
    """
    Downloads Instagram video using yt-dlp.
    """
    # Naming format: monitors_2/video_1_ID.mp4
    output_template = os.path.join(OUTPUT_DIR, f"video_{index}_%(id)s.%(ext)s")
    
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
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   [SUCCESS] {index}: Downloaded {url}")
            return True
        else:
            # Check if it's a private video/login issue
            error_msg = result.stderr.split('\n')[0]
            print(f"   [FAILED] {index}: {error_msg}")
            return False
    except Exception as e:
        print(f"   [ERROR] Runtime error on link {index}: {e}")
        return False

def main():
    check_setup()

    # Read links from file
    with open(INPUT_FILE, "r") as f:
        # filter(None, ...) removes empty lines
        links = [line.strip() for line in f if line.strip()]

    if not links:
        print(f"[IDLE] No links found in {INPUT_FILE}. Exiting.")
        return

    print(f"--- Starting Batch Download ({len(links)} links) ---\n")
    
    success_count = 0
    for i, link in enumerate(links, start=1):
        if run_yt_dlp(link, i):
            success_count += 1

    print(f"\n--- FINISHED ---")
    print(f"Total processed: {len(links)}")
    print(f"Successfully saved to '{OUTPUT_DIR}': {success_count}")

if __name__ == "__main__":
    main()