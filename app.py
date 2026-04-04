import os
import tempfile
import shutil
import yt_dlp
from flask import Flask, render_template, request, send_file
from flask_socketio import SocketIO

app = Flask(__name__)
# 'gevent' allows the progress bar to update while the download happens
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='gevent')

# This function grabs the progress from yt-dlp and sends it to the web page
def progress_hook(d):
    if d['status'] == 'downloading':
        # Clean the percentage string (e.g., '45.2%' -> '45.2')
        p = d.get('_percent_str', '0%').replace('%', '').strip()
        socketio.emit('progress_update', {'percent': p})
    elif d['status'] == 'finished':
        socketio.emit('progress_update', {'percent': '100'})

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('start_process')
def handle_process(data):
    video_url = data.get('url')
    start_t = data.get('start_time')
    end_t = data.get('end_time')

    temp_dir = tempfile.mkdtemp()
    base_name = "clipped_audio"
    output_path_mp3 = os.path.join(temp_dir, f"{base_name}.mp3")

    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'progress_hooks': [progress_hook],
        'external_downloader': 'ffmpeg',
        'external_downloader_args': {
            'ffmpeg_i': ['-ss', start_t, '-to', end_t, '-loglevel', 'error']
        },
        'extractor_args': {
            'youtube': {
                'js_runtimes': 'node',
                'player_client': ['android', 'web']
            }
        },
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(temp_dir, f'{base_name}.%(ext)s'),
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        # Trigger the download on the user's browser
        socketio.emit('processing_finished', {'file_url': f'/download_file?path={output_path_mp3}'})
    except Exception as e:
        socketio.emit('error', {'msg': str(e)})

@app.route('/download_file')
def download_file():
    path = request.args.get('path')
    # Use after_this_request or similar logic if you want to delete temp_dir immediately
    return send_file(path, as_attachment=True, download_name="clip.mp3")

if __name__ == '__main__':
    # Render provides the PORT variable automatically
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)