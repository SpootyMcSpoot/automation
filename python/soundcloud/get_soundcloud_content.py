import os
import argparse
import requests
from bs4 import BeautifulSoup
import logging
import subprocess
import glob 
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# python get_soundcloud_content.py <playlist_url> <save_directory> --mode playlist
# python get_soundcloud_content.py <profile_url> <save_directory> --mode profile

# Logging setup
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("scraping_log.txt", 'w', 'utf-8'), logging.StreamHandler()])


def get_name_from_url(url):
    """Fetch the name of the SoundCloud playlist or user profile using web scraping."""
    logging.info("Fetching the name from URL: %s", url)

    response = requests.get(url)
    if response.status_code != 200:
        logging.error(
            "Failed to fetch the page for the URL: %s. Using 'Unknown_Name' as default.", url)
        return "Unknown_Name"

    soup = BeautifulSoup(response.content, 'html.parser')
    title_tag = soup.find("meta", property="og:title")
    if title_tag:
        name = title_tag.get("content", "Unknown_Name")
        logging.info("Fetched name: %s", name)
        return name

    logging.warning(
        "Couldn't determine the name from the URL: %s. Using 'Unknown_Name' as default.", url)
    return "Unknown_Name"


def get_profile_track_urls(profile_url):
    logging.info("Fetching track URLs from the profile: %s", profile_url)

    options = webdriver.ChromeOptions()
    options.headless = True  # Runs Chrome in headless mode.
    options.add_argument('--no-sandbox')  # # Bypass OS security model
    options.add_argument('start-maximized')  # Start maximized
    options.add_argument('disable-infobars')
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(profile_url)

        # Assuming tracks take a maximum of 10 seconds to load (this can be adjusted)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "a[href*='/tracks/']")))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        logging.debug("Returned HTML content:\n%s", soup.prettify())

        track_links = [a['href'] for a in soup.find_all(
            'a', href=True) if '/tracks/' in a['href'] and 'soundcloud.com' not in a['href']]
        track_urls = ['https://soundcloud.com' + link for link in track_links]

        logging.info("Found %d track URLs.", len(track_urls))
        for i, track_url in enumerate(track_urls, 1):
            logging.debug("Track %d URL: %s", i, track_url)

        return track_urls
    except Exception as e:
        logging.error("Error while fetching track URLs: %s", e)
        return []
    finally:
        driver.quit()


def track_already_downloaded(track_url, save_path):
    """Check if a track has already been downloaded by checking its presence in the save directory."""
    track_name = get_name_from_url(track_url).replace(' ', '_')  # Convert spaces to underscores
    # Search for files starting with the track name in the save directory
    matching_files = glob.glob(os.path.join(save_path, f"{track_name}*"))
    return len(matching_files) > 0

def download_soundcloud_content(url, directory, mode):
    logging.info(f"Starting download process for mode: {mode}.")
    
    name = get_name_from_url(url)
    save_path = os.path.join(directory, name)

    # Ensure the directory exists
    if not os.path.exists(save_path):
        logging.info(f"Creating directory: {save_path}")
        os.makedirs(save_path)
    else:
        logging.info(f"Saving to existing directory: {save_path}")

    if mode == "playlist":
        cmd = ['scdl', '-l', url, '-c', '--path', save_path]
        logging.info("Running scdl command for playlist: %s", ' '.join(cmd))
        subprocess.run(cmd)
    elif mode == "profile":
        track_urls = get_profile_track_urls(url)
        for track_url in track_urls:
            if not track_already_downloaded(track_url, save_path):  # Check if the track has already been downloaded
                cmd = ['scdl', '-l', track_url, '-c', '--path', save_path]
                logging.info("Running scdl command for track: %s", ' '.join(cmd))
                subprocess.run(cmd)
            else:
                logging.info(f"Track {track_url} seems to be already downloaded. Skipping.")

    logging.info("Download process completed.")


parser = argparse.ArgumentParser(
    description="Download content from SoundCloud.")
parser.add_argument(
    'url', type=str, help="URL of the SoundCloud content to download.")
parser.add_argument('directory', type=str,
                    help="Directory to save the downloaded content.")
parser.add_argument('--mode', choices=['playlist', 'profile'],
                    default='playlist', help="Mode of the download: 'playlist' or 'profile'.")

args = parser.parse_args()
download_soundcloud_content(args.url, args.directory, args.mode)
