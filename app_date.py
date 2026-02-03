import subprocess
import json
import os
import time
from datetime import datetime

# --- Configuration ---
VIEW_THRESHOLD = 20000  
DOWNLOAD_LIMIT = 20      
START_DATE = "20250301"  # Format: YYYYMMDD (March 1st, 2025)
# ---------------------

OUTPUT_DIR = "tiktok_downloads"
COOKIE_FILE = os.path.join(os.getcwd(), 'cookies.txt')

def run_yt_dlp(url, options, silent=False):
    """ Runs yt-dlp with impersonation to bypass blocks. """
    # Using 'chrome' impersonation to avoid the extraction errors you saw earlier
    cmd = ['yt-dlp', '--impersonate', 'chrome', url] + options
    
    if os.path.exists(COOKIE_FILE):
        cmd.extend(['--cookies', COOKIE_FILE])

    try:
        process = subprocess.run(
            cmd, capture_output=True, text=True, check=True, encoding='utf-8'
        )
        return process.stdout
    except subprocess.CalledProcessError as e:
        if not silent:
            print(f"\n[ERROR] Extraction failed. Error: {e.stderr}")
        raise Exception(f"yt-dlp failed: {e.stderr}")

def get_metadata(tiktok_url):
    """ Extracts metadata including upload dates. """
    print(f"STEP 1: Extracting metadata for {tiktok_url}...")
    
    options = ['--dump-json', '--flat-playlist']
    stdout = run_yt_dlp(tiktok_url, options, silent=False)
    
    video_entries = []
    for line in stdout.splitlines():
        try:
            data = json.loads(line)
            # yt-dlp usually provides 'upload_date' in YYYYMMDD format
            upload_date = data.get('upload_date') 
            view_count = data.get('view_count') or 0
            
            video_entries.append({
                'url': data.get('webpage_url') or data.get('url'),
                'title': data.get('title', 'Untitled'),
                'view_count': view_count,
                'upload_date': upload_date  # e.g., "20250315"
            })
        except json.JSONDecodeError:
            continue
            
    print(f"Successfully found {len(video_entries)} total videos.")
    return video_entries

def filter_and_sort(video_entries):
    """ Filters by views AND date (March 2025 onwards). """
    print(f"\nSTEP 2: Filtering (Views > {VIEW_THRESHOLD:,} AND Date >= {START_DATE})...")

    filtered_videos = []
    for v in video_entries:
        # Check views
        view_match = v['view_count'] >= VIEW_THRESHOLD
        
        # Check date (ensure date exists and is >= March 1st)
        date_match = v['upload_date'] and v['upload_date'] >= START_DATE
        
        if view_match and date_match:
            filtered_videos.append(v)

    # Sort by views
    sorted_videos = sorted(
        filtered_videos, key=lambda x: x['view_count'], reverse=True
    )
    
    final_list = sorted_videos[:DOWNLOAD_LIMIT]
    print(f"   -> Found {len(filtered_videos)} videos meeting BOTH criteria.")
    print(f"   -> Selecting the top {len(final_list)} for download.")
    return final_list

def download_videos(final_list):
    """ Downloads the final filtered list. """
    print("\n" + "="*60)
    print(f"STEP 3: Downloading {len(final_list)} videos...")
    print("="*60)

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for i, video in enumerate(final_list):
        date_str = video['upload_date'] if video['upload_date'] else "UnknownDate"
        print(f"\n[{i + 1}/{len(final_list)}] [{date_str}] Downloading: {video['title'][:40]}...")
        
        output_template = os.path.join(
            OUTPUT_DIR, 
            f"viral_{i+1:02d}_%(view_count)s_%(upload_date)s_%(id)s.%(ext)s"
        )

        options = [
            '-o', output_template,
            '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]', 
        ]
        
        try:
            run_yt_dlp(video['url'], options, silent=True)
            print(f"    -> Success!")
        except Exception:
            print(f"    -> Skipping video {i+1}. It might be private or region-locked.")

def main():
    tiktok_url = input("Enter TikTok Profile URL: ").strip()
    if not tiktok_url: return

    try:
        all_videos = get_metadata(tiktok_url)
        if not all_videos:
            print("No metadata found.")
            return

        viral_videos = filter_and_sort(all_videos)
        if not viral_videos:
            print(f"No videos found matching those criteria.")
            return

        download_videos(viral_videos)
        print(f"\nPROCESS COMPLETE. Check the '{OUTPUT_DIR}' folder.")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    main()