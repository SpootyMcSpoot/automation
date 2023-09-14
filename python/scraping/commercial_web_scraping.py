import os
import re
import requests
from bs4 import BeautifulSoup
from time import sleep
import logging

BASE_URL = 'https://www.retrojunk.com/commercials'
DOWNLOAD_DIR = '/path/to/your/directory/'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
}

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def get_video_page_links():
    # Implement logic to get all links to video pages
    pass


def download_video(video_url, filename):
    response = requests.get(video_url, headers=headers, stream=True)
    with open(filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)


def scraper():
    links = get_video_page_links()

    for link in links:
        logging.info(f"Processing link: {link}")
        response = requests.get(link, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract video title (you might need to adjust this logic)
        video_title = os.path.basename(link)

        # Extract aired date
        aired_data = soup.find('div', text=re.compile(
            'Aired:')).next_sibling.strip()
        decade = aired_data[:3] + '0s'

        # Construct directory path
        decade_dir = os.path.join(DOWNLOAD_DIR, decade)
        if not os.path.exists(decade_dir):
            os.makedirs(decade_dir)

        # Check if file already exists
        filepath = os.path.join(decade_dir, video_title + '.mp4')
        if os.path.exists(filepath):
            logging.info(f"File {filepath} already exists. Skipping.")
            continue

        # Locate the video file link
        # Note: This logic is a placeholder, you'll need to update this part
        video_link = soup.find('video_tag_or_logic_to_find_link').get('src')

        # Download the video
        download_video(video_link, filepath)
        logging.info(f"Downloaded video to {filepath}")

        # Implement rate-limiting logic
        sleep(5)


scraper()
