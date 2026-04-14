import yt_dlp
import subprocess
import os
import uuid
import tempfile
from urllib.parse import parse_qs

DOWNLOAD_FOLDER = "/tmp"  # Use /tmp for serverless

def download_audio_segment(url, start_time, end_time):
    file_id = str(uuid.uuid4())
    temp_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")
    output_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.mp3")

    ydl_opts = {
        'format': 'worstaudio',
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

def handler(event, context):
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    }
    
    if event['httpMethod'] == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    if event['httpMethod'] != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': 'Method Not Allowed'
        }

    try:
        # Parse the body
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')

        params = parse_qs(body)
        url = params.get('url', [None])[0]
        start = params.get('start', [None])[0]
        end = params.get('end', [None])[0]

        if not all([url, start, end]):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': 'Missing parameters: url, start, end'
            }

        output_file = download_audio_segment(url, start, end)
        with open(output_file, 'rb') as f:
            file_data = f.read()
        os.remove(output_file)

        import base64
        encoded_data = base64.b64encode(file_data).decode('utf-8')

        response_headers = {
            'Content-Type': 'audio/mpeg',
            'Content-Disposition': 'attachment; filename="cut_audio.mp3"',
            'Access-Control-Allow-Origin': '*',
        }

        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': encoded_data,
            'isBase64Encoded': True
        }
    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\n{traceback.format_exc()}"
        return {
            'statusCode': 500,
            'headers': headers,
            'body': error_msg
        }