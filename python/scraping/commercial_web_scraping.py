import os
import argparse
from urllib import request, error
from bs4 import BeautifulSoup
from time import sleep
import logging
from tqdm import tqdm

base_url_retro = 'https://www.retrojunk.com'
base_url_archive = 'https://archive.org/search?query=subject%3A%22'
country = 'japan'
download_dir = os.path.join('./commercials', country)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
}

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

parser = argparse.ArgumentParser(description='Scraper for commercials')
parser.add_argument('--source', choices=['retrojunk', 'archive'],
                    required=True, help='Specify the source website for scraping')
args = parser.parse_args()


def get_video_page_links(page_url):
    logging.debug(f"Fetching content from URL: {page_url}")
    req = request.Request(page_url, headers=headers)

    try:
        response = request.urlopen(req)
        html_content = response.read()
        soup = BeautifulSoup(html_content, 'html.parser')
        logging.debug("Successfully fetched and parsed the content.")
    except error.HTTPError as e:
        logging.error(
            f"HTTPError while fetching content from {page_url}: {e.code} {e.reason}")
        return [], None
    except error.URLError as e:
        logging.error(
            f"URLError while fetching content from {page_url}: {e.reason}")
        return [], None

    links = [base_url_retro + link.get('href')
             for link in soup.find_all('a', class_='title-link')]
    current_page = soup.find('a', class_='pagination-link is-current')
    next_page_url = None

    if current_page:
        try:
            next_page_num = int(current_page.text) + 1
            next_page_url = base_url_retro + \
                f'/commercials?page={next_page_num}'
            logging.debug(
                f"Next page determined using pagination list: {next_page_url}")
        except ValueError:
            logging.debug(
                "Could not determine next page from pagination list.")

    return links, next_page_url


def download_video(video_url, filename):
    logging.debug(f"Attempting to download from URL: {video_url}")
    req = request.Request(video_url, headers=headers)

    try:
        response = request.urlopen(req)
        total_size = int(response.getheader('Content-Length', 0))

        with open(filename, 'wb') as file:
            for data in tqdm(iter(lambda: response.read(8192), b''), desc=f"Downloading {filename}", total=total_size//8192, unit="KB"):
                file.write(data)
        logging.debug(f"Downloaded {filename} successfully.")
    except error.HTTPError as e:
        logging.error(
            f"HTTPError while downloading {video_url}: {e.code} {e.reason}")
    except error.URLError as e:
        logging.error(f"URLError while downloading {video_url}: {e.reason}")


def get_aired_decade(soup):
    aired_divs = soup.find_all('div')

    for div in aired_divs:
        if 'Aired:' in div.get_text():
            year_text = div.get_text().replace('Aired:', '').strip().replace('"', '')

            try:
                year = int(year_text)
                return str(year // 10 * 10) + 's'
            except ValueError:
                continue

    return None


def scraper():
    next_page_url = base_url_retro + '/commercials'

    while next_page_url:
        links, next_page_url = get_video_page_links(next_page_url)

        for link in links:
            req = request.Request(link, headers=headers)
            try:
                response = request.urlopen(req)
                soup = BeautifulSoup(response.read(), 'html.parser')
                decade = get_aired_decade(soup)

                if not decade:
                    logging.warning(
                        f"Could not determine aired decade for link: {link}")
                    continue

                decade_dir = os.path.join(download_dir, decade)
                os.makedirs(decade_dir, exist_ok=True)

                video_title = link.split('/')[-1]
                video_source_tag = soup.find('source', type='video/mp4')

                if video_source_tag:
                    video_link = video_source_tag.get('src')
                    filepath = os.path.join(decade_dir, video_title + '.mp4')

                    if os.path.exists(filepath):
                        logging.info(
                            f"File {filepath} already exists. Skipping.")
                        continue

                    download_video(video_link, filepath)
                    sleep(15)
                else:
                    logging.warning(f"No video source found for link: {link}")
            except error.HTTPError as e:
                logging.error(
                    f"HTTPError while processing link {link}: {e.code} {e.reason}")
            except error.URLError as e:
                logging.error(
                    f"URLError while processing link {link}: {e.reason}")


def run_scraper():
    if args.source == "retrojunk":
        scraper()
    elif args.source == "archive":
        # Call the function for scraping archive.org here
        pass


run_scraper()
