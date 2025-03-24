from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from image_scraper.downloader import download_image

def scrape_images(url, folder_path):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tags = soup.find_all('img')

        image_data = []
        
        for img in img_tags:
            img_url = img.get('src')
            if not img_url:
                continue
            img_url = urljoin(url, img_url)
            file_path = download_image(img_url, folder_path)
            
            if file_path:
                deepfake_flag = 'Pending'
                image_data.append([img_url, file_path, deepfake_flag])
        
        return image_data
    except Exception as e:
        print(f"Failed to scrape images: {e}")
        return []
