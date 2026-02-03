import subprocess
import os
import time

# --- CONFIG ---
COOKIE_FILE = "tiktok_cookies.txt"
LINKS_FILE = "links.txt"
OUTPUT_DIR = "tiktok_final_exports"
# --------------

def process_videos():
    if not os.path.exists(LINKS_FILE):
        print(f"❌ Error: {LINKS_FILE} not found.")
        return

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(LINKS_FILE, "r") as f:
        links = [line.strip() for line in f.readlines() if line.strip()]

    print(f"🚀 Processing {len(links)} links. Quality: Max | Output: MOV | Captions: Included")

    for i, link in enumerate(links):
        print(f"\n--- [{i+1}/{len(links)}] Target: {link} ---")
        
        # We use a specific ID to keep track of files during conversion
        video_id = f"tiktok_{i+1}"
        description_file = os.path.join(OUTPUT_DIR, f"{video_id}.description")
        temp_mp4 = os.path.join(OUTPUT_DIR, f"{video_id}_temp.mp4")
        final_mov = os.path.join(OUTPUT_DIR, f"{video_id}.mov")

        # 1. DOWNLOAD BEST QUALITY + CAPTION
        cmd_download = [
            "yt-dlp",
            "--impersonate", "chrome",
            "--cookies", COOKIE_FILE,
            # Using a custom API hostname helps bypass regional extraction blocks
            "--extractor-args", "tiktok:api_hostname=api16-normal-c-useast1a.tiktokv.com",
            "-f", "bv*+ba/b", 
            "--write-description",
            "-o", temp_mp4,
            link
        ]
        
        try:
            # Run download
            result = subprocess.run(cmd_download, capture_output=True, text=True)
            
            if result.returncode != 0:
                if "Unable to extract" in result.stderr:
                    print(f"❌ Extraction blocked by TikTok for this link. Skipping.")
                else:
                    print(f"❌ Error: {result.stderr.strip()[:100]}")
                continue

            # 2. CONVERT TO MOV (Fast Stream Copy)
            if os.path.exists(temp_mp4):
                print(f"🔄 Converting to MOV...")
                cmd_convert = [
                    "ffmpeg", "-i", temp_mp4,
                    "-c", "copy", # No quality loss, super fast
                    "-f", "mov",
                    final_mov,
                    "-y"
                ]
                subprocess.run(cmd_convert, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                # Cleanup temp file
                os.remove(temp_mp4)
                print(f"✅ Success! Saved to {final_mov}")
            
        except Exception as e:
            print(f"⚠️ Unexpected error: {e}")
        
        # Random delay (3-6s) is critical to avoid being flagged as a bot
        time.sleep(5)

if __name__ == "__main__":
    process_videos()