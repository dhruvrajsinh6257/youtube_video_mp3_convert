import requests
import time

time.sleep(2)

url = 'http://localhost:5000/api/download'
data = {'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}

try:
    print("Testing download endpoint...")
    response = requests.post(url, data=data, timeout=30)
    print(f'Status Code: {response.status_code}')
    
    if response.status_code != 200:
        print(f'ERROR RESPONSE:')
        print(response.text[:2000])
    else:
        print(f'SUCCESS! Downloaded {len(response.content)} bytes')
        print('File starts with:', response.content[:20])
        
except Exception as e:
    print(f'Exception: {str(e)}')
    import traceback
    traceback.print_exc()
