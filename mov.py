import subprocess
import os

# --- Configuration ---
INPUT_DIR = "videos_to_convert"
OUTPUT_DIR = "iphone_ready_videos"

def convert_to_iphone_mov():
    # Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # Get list of mp4 files
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.mp4')]

    if not files:
        print(f"No MP4 files found in {INPUT_DIR}")
        return

    print(f"Found {len(files)} videos. Starting conversion...")

    for filename in files:
        input_path = os.path.join(INPUT_DIR, filename)
        # Create output name by swapping extension
        output_filename = os.path.splitext(filename)[0] + ".mov"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"Converting: {filename} -> {output_filename}")

        # FFmpeg command:
        # -c:v libx264 (H.264 video)
        # -preset slow (Better quality/compression)
        # -crf 22 (High quality balance)
        # -c:a aac (iPhone friendly audio)
        # -pix_fmt yuv420p (Ensures compatibility with Apple QuickTime)
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'slow',
            '-crf', '22',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            output_path,
            '-y' # Overwrite if exists
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Successfully converted {filename}")
        except subprocess.CalledProcessError as e:
            print(f"Error converting {filename}: {e.stderr.decode()}")

if __name__ == "__main__":
    # Ensure the input folder exists for the user to put files in
    if not os.path.exists(INPUT_DIR):
        os.makedirs(INPUT_DIR)
        print(f"Created '{INPUT_DIR}' folder. Put your MP4s there and run again.")
    else:
        convert_to_iphone_mov()