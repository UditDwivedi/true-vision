import os
import requests
from PIL import Image
import io
import hashlib

def download_image(image_url, folder_path):
    try:
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        image_content = response.content
        image_file = Image.open(io.BytesIO(image_content)).convert('RGB')
        image_name = hashlib.sha1(image_content).hexdigest()[:10] + '.jpg'
        file_path = os.path.join(folder_path, image_name)
        
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        with open(file_path, 'wb') as file:
            image_file.save(file, 'JPEG', quality=85)
        
        print(f"Downloaded: {file_path}")
        return file_path
    except Exception as e:
        print(f"Failed to download {image_url}: {e}")
        return None
