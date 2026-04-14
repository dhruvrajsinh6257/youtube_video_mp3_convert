from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import uuid
from pydub import AudioSegment

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


def download_and_convert_to_wav(url):
    """Download audio from YouTube URL and try to convert to WAV"""
    try:
        file_id = str(uuid.uuid4())
        temp_file = f"{DOWNLOAD_FOLDER}/{file_id}"
        
        ydl_opts = {
            'format': 'worstaudio/best',
            'outtmpl': temp_file,
            'quiet': True,
            'noplaylist': True,
            '_js_runtimes': ['node'],
        }
        
        # Download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
        
        if not os.path.exists(downloaded_file):
            raise Exception("Audio file not found after download")
        
        # Try to convert to WAV, but fall back to original if ffmpeg not available
        try:
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
            # ffmpeg not available, return original format
            return downloaded_file
                
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
        
        # Download and optionally convert to WAV
        audio_file = download_and_convert_to_wav(url)
        
        # Determine file type
        file_ext = os.path.splitext(audio_file)[1].lower()
        mime_type = "audio/mpeg" if file_ext in [".m4a", ".aac"] else "audio/wav"
        download_name = f"audio{file_ext}"
        
        # Send file
        return send_file(audio_file, as_attachment=True, download_name=download_name, mimetype=mime_type)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)