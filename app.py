from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import uuid
from pydub import AudioSegment

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def download_and_convert_to_wav(url):
    """Download audio from YouTube URL and convert to WAV"""
    try:
        file_id = str(uuid.uuid4())
        temp_file = f"{DOWNLOAD_FOLDER}/{file_id}"
        
        ydl_opts = {
            'format': 'worstaudio/best',
            'outtmpl': temp_file,
            'quiet': True,
            'noplaylist': True,
        }
        
        # Download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
        
        if not os.path.exists(downloaded_file):
            raise Exception("Audio file not found after download")
        
        # Convert to WAV using pydub
        audio = AudioSegment.from_file(downloaded_file)
        wav_file = f"{DOWNLOAD_FOLDER}/{file_id}.wav"
        audio.export(wav_file, format="wav")
        
        # Clean up original
        try:
            os.remove(downloaded_file)
        except:
            pass
        
        return wav_file
                
    except Exception as e:
        raise Exception(f"Download error: {str(e)}")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/api/download", methods=["POST", "OPTIONS"])
def download():
    if request.method == "OPTIONS":
        return "", 200
    
    try:
        url = request.form.get("url")
        
        if not url:
            return jsonify({"error": "Missing YouTube URL"}), 400
        
        # Download and convert to WAV
        wav_file = download_and_convert_to_wav(url)
        
        # Send file
        return send_file(wav_file, as_attachment=True, download_name="audio.wav", mimetype="audio/wav")
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)