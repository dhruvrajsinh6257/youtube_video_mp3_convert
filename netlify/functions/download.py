import yt_dlp
import os
import uuid
import json
from urllib.parse import parse_qs
from pydub import AudioSegment

DOWNLOAD_FOLDER = "/tmp"

def download_and_convert_to_wav(url):
    """Download audio from YouTube URL and try to convert to WAV"""
    try:
        file_id = str(uuid.uuid4())
        temp_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}")
        
        ydl_opts = {
            'format': 'worstaudio/best',
            'outtmpl': temp_file,
            'quiet': True,
            'noplaylist': True,
            'no_warnings': True,
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
            wav_file = os.path.join(DOWNLOAD_FOLDER, f"{file_id}.wav")
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
            'headers': {**headers, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method Not Allowed'})
        }

    try:
        # Parse form data
        body = event.get('body', '')
        if event.get('isBase64Encoded'):
            import base64
            body = base64.b64decode(body).decode('utf-8')
        
        params = parse_qs(body)
        url = params.get('url', [None])[0]
        
        if not url:
            return {
                'statusCode': 400,
                'headers': {**headers, 'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Missing YouTube URL'})
            }
        
        # Download and optionally convert to WAV
        audio_file = download_and_convert_to_wav(url)
        
        with open(audio_file, 'rb') as f:
            file_data = f.read()
        
        # Try to clean up
        try:
            os.remove(audio_file)
        except:
            pass
        
        import base64
        encoded_data = base64.b64encode(file_data).decode('utf-8')
        
        # Determine file type and MIME type
        file_ext = os.path.splitext(audio_file)[1].lower()
        mime_type = "audio/mpeg" if file_ext in [".m4a", ".aac"] else "audio/wav"
        download_name = f"audio{file_ext}"
        
        response_headers = {
            'Content-Type': mime_type,
            'Content-Disposition': f'attachment; filename="{download_name}"',
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
        error_msg = str(e)
        return {
            'statusCode': 500,
            'headers': {**headers, 'Content-Type': 'application/json'},
            'body': json.dumps({'error': error_msg})
        }