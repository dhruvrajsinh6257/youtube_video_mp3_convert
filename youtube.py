import yt_dlp
import os

def download_and_cut_audio():
    print("\n" + "="*45)
    print("--- High-Efficiency YouTube Audio Cutter ---")
    print("="*45)
    
    # 1. User Inputs
    url = input("\nEnter the YouTube URL: ").strip()
    if not url:
        print("❌ Error: URL cannot be empty.")
        return

    print("\nNote: For long videos, use HH:MM:SS (e.g., 01:10:20)")
    start_t = input("Enter Start Time: ").strip()
    end_t = input("Enter End Time: ").strip()
    
    output_final = "final_cut_output.mp3"

    # 2. Configure yt-dlp
    ydl_opts = {
        # 'bestaudio' keeps the file size small and download fast
        'format': 'bestaudio/best',
        'noplaylist': True,
        
        # FIX: JavaScript Runtime & Client issues
        'extractor_args': {
            'youtube': {
                'js_runtimes': 'node',  # Uses your installed Node.js
                'player_client': ['android', 'web']
            }
        },

        # FIX: "Read operation timed out" for 4-hour videos
        # We tell ffmpeg to ONLY download the segment we want.
        'external_downloader': 'ffmpeg',
        'external_downloader_args': {
            'ffmpeg_i': [
                '-ss', start_t, 
                '-to', end_t,
                '-loglevel', 'error'  # Keeps the console clean
            ]
        },

        # Conversion to MP3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        
        'outtmpl': 'temp_result.%(ext)s',
        
        # Optional: Cookies help avoid 403 Forbidden/Sign-in errors
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }

    try:
        print(f"\n[Step 1/2] Fetching segment: {start_t} to {end_t}...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # [Step 2/2] Finalizing file name
        # yt-dlp's ExtractAudio postprocessor will turn temp_result.webm/mp4 into temp_result.mp3
        if os.path.exists("temp_result.mp3"):
            if os.path.exists(output_final):
                os.remove(output_final)
            os.rename("temp_result.mp3", output_final)
            print(f"\n✅ Success! File saved as: {output_final}")
        else:
            print("\n❌ Error: The MP3 file was not generated correctly.")
        
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        print("\nTIP: If you get a '403 Forbidden' error, ensure you have a 'cookies.txt' in this folder.")

if __name__ == "__main__":
    # Ensure Node.js is recognized
    # If this script still shows the JS warning, try restarting VS Code.
    download_and_cut_audio()