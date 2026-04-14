import yt_dlp
import os
import uuid
from urllib.parse import parse_qs
from pydub import AudioSegment
import io

DOWNLOAD_FOLDER = "/tmp"

def download_audio_segment(url, start_time, end_time):
    try:
        file_id = str(uuid.uuid4())
        temp_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.%(ext)s")
        
        # Download audio
        ydl_opts = {
            'format': 'worstaudio/best',
            'outtmpl': temp_file,
            'quiet': True,
            'noplaylist': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
        
        # Convert time strings to milliseconds
        def time_to_ms(time_str):
            parts = time_str.split(':')
            hours = int(parts[0]) if len(parts) > 2 else 0
            minutes = int(parts[-2]) if len(parts) > 1 else 0
            seconds = int(parts[-1].split('.')[0]) if len(parts) > 0 else 0
            return (hours * 3600 + minutes * 60 + seconds) * 1000
        
        start_ms = time_to_ms(start_time)
        end_ms = time_to_ms(end_time)
        
        # Load audio with pydub
        audio = AudioSegment.from_file(downloaded_file)
        
        # Extract segment
        cut_audio = audio[start_ms:end_ms]
        
        # Export to MP3
        output_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}_cut.mp3")
        cut_audio.export(output_file, format="mp3", bitrate="128k")
        
        # Clean up original
        os.remove(downloaded_file)
        
        return output_file
    except Exception as e:
        raise Exception(f"Audio processing error: {str(e)}")

def handler(event, context):
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
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
        # Parse form data
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        
        # Handle both URL-encoded and multipart form data
        if 'application/x-www-form-urlencoded' in event.get('headers', {}).get('content-type', ''):
            params = parse_qs(body)
            url = params.get('url', [None])[0]
            start = params.get('start', [None])[0]
            end = params.get('end', [None])[0]
        else:
            # Simple form parsing for multipart
            lines = body.split('\n')
            url = start = end = None
            for line in lines:
                if 'name="url"' in line and len(lines) > lines.index(line) + 2:
                    url = lines[lines.index(line) + 2].strip()
                elif 'name="start"' in line and len(lines) > lines.index(line) + 2:
                    start = lines[lines.index(line) + 2].strip()
                elif 'name="end"' in line and len(lines) > lines.index(line) + 2:
                    end = lines[lines.index(line) + 2].strip()
        
        if not all([url, start, end]):
            return {
                'statusCode': 400,
                'headers': {**headers, 'Content-Type': 'text/plain'},
                'body': f'Missing parameters. Got url={url}, start={start}, end={end}'
            }
        
        output_file = download_audio_segment(url, start, end)
        
        with open(output_file, 'rb') as f:
            file_data = f.read()
        
        os.remove(output_file)
        
        import base64
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        
        response_headers = {
            **headers,
            'Content-Type': 'audio/mpeg',
            'Content-Disposition': 'attachment; filename="cut_audio.mp3"',
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
            'headers': {**headers, 'Content-Type': 'text/plain'},
            'body': error_msg
        }