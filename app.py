from flask import Flask, render_template, request, send_file
import yt_dlp
import subprocess
import os
import uuid

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def download_audio_segment(url, start_time, end_time):
    file_id = str(uuid.uuid4())
    temp_file = f"{DOWNLOAD_FOLDER}/{file_id}.%(ext)s"
    output_file = f"{DOWNLOAD_FOLDER}/{file_id}.mp3"

    ydl_opts = {
        'format': 'worstaudio',  # fast download
        'outtmpl': temp_file,
        'quiet': True,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        downloaded_file = ydl.prepare_filename(info)

    # Cut using ffmpeg
    command = [
        "ffmpeg",
        "-y",
        "-i", downloaded_file,
        "-ss", start_time,
        "-to", end_time,
        "-vn",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        output_file
    ]

    subprocess.run(command, check=True)

    os.remove(downloaded_file)

    return output_file


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form["url"]
        start = request.form["start"]
        end = request.form["end"]

        output_file = download_audio_segment(url, start, end)
        return send_file(output_file, as_attachment=True)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)