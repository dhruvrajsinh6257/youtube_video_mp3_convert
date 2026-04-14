import yt_dlp
import subprocess
import os

def download_audio_segment_fast(url, start_time, end_time):
    temp_file = "temp_audio.%(ext)s"
    output_file = "output.mp3"

    ydl_opts = {
        # 🔥 Get LOW SIZE audio (fast)
        'format': 'worstaudio',  
        'outtmpl': temp_file,
        'quiet': False,
        'noplaylist': True,
    }

    try:
        print("\n⚡ Downloading LOW-SIZE audio (fast)...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)

        print(f"✅ Downloaded: {downloaded_file}")

        print("\n✂️ Cutting and converting to MP3...")

        command = [
            "ffmpeg",
            "-y",
            "-i", downloaded_file,
            "-ss", start_time,
            "-to", end_time,
            "-vn",
            "-acodec", "libmp3lame",
            "-ab", "128k",   # lower bitrate = faster + smaller
            output_file
        ]

        subprocess.run(command, check=True)

        print(f"\n🎉 Done! Saved as: {output_file}")

        os.remove(downloaded_file)

    except Exception as e:
        print("\n❌ Error:", str(e))


if __name__ == "__main__":
    print("\n--- ⚡ FAST YouTube Audio Cutter ---\n")

    url = input("Enter the YouTube URL: ").strip()

    print("\nNote: Use HH:MM:SS format (e.g., 01:15:30)")
    start_time = input("Enter Start Time: ").strip()
    end_time = input("Enter End Time: ").strip()

    download_audio_segment_fast(url, start_time, end_time)