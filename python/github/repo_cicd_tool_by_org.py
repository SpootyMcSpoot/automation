# Importing necessary modules
import requests
import pandas as pd
import logging
import queue
import time
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor
from time import sleep

# Define the names of organizations to analyze and your API key
load_dotenv()  # take environment variables from .env.
api_key = os.getenv('api_key')
org_names = ['example1', 'example2']
outputfile = 'cicd_report.xlsx'
# Set this to true if you want to download and save CI/CD configuration files
dump_cicd_configs = True

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
urllib3_logger = logging.getLogger('urllib3')
urllib3_logger.setLevel(logging.INFO)

# Prepare headers for API requests, using the provided API key
headers = {'Authorization': f'token {api_key}'}

# Initialize a queue to store results
row_queue = queue.Queue()

# Initialize GitHub API rate limit and reset time
rate_limit_remaining = 5000
rate_limit_reset = time.time()

# Define CI/CD tools and their respective configuration file paths
tools = {
    "Travis CI": ".travis.yml",
    "CircleCI": ".circleci/config.yml",
    "Jenkins": "Jenkinsfile",
    "GitHub Actions": ".github/workflows",
    "Bamboo": "bamboo-specs/bamboo.yml",
}

# Function to update GitHub API rate limit and sleep if needed


def update_rate_limit(response):
    global rate_limit_remaining, rate_limit_reset
    if 'X-RateLimit-Remaining' in response.headers and 'X-RateLimit-Reset' in response.headers:
        rate_limit_remaining = int(response.headers['X-RateLimit-Remaining'])
        rate_limit_reset = int(response.headers['X-RateLimit-Reset'])
        if rate_limit_remaining < 20:
            sleep_time = max(rate_limit_reset - time.time(), 0)
            if sleep_time > 0:
                logging.info(
                    f"Rate limit close to being exceeded, sleeping for {sleep_time} seconds.")
                sleep(sleep_time)

# Function to process each repo and identify the CI/CD tool used, based on the presence of certain config files


def process_repo(repo, index, total_repos):
    logging.info(f"Starting processing of repo: {repo['name']}")
    try:
        repo_name = repo['name']
        detected_tools = []
        base_contents_url = repo['contents_url'].replace("{+path}", "")
        permission_denied = False

        for tool, config_file in tools.items():
            logging.info(f"Checking for {tool} in {repo_name}")
            tool_url = base_contents_url + config_file
            response = requests.get(tool_url, headers=headers, timeout=(5, 14))
            update_rate_limit(response)

            # Add the CI/CD tool to detected_tools list if its config file is found
            # If dump_cicd_configs is True, download the config files as well
            if response.status_code == 200:
                detected_tools.append(tool)
                if dump_cicd_configs:
                    os.makedirs(tool, exist_ok=True)
                    if tool == "GitHub Actions":  # For GitHub Actions, download all files in the workflow directory
                        config_files = response.json()
                        for config in config_files:
                            download_url = config['download_url']
                            file_name = os.path.join(
                                tool, repo_name, config['name'])
                            os.makedirs(os.path.dirname(
                                file_name), exist_ok=True)
                            with requests.get(download_url, stream=True) as r:
                                r.raise_for_status()
                                with open(file_name, 'wb') as f:
                                    for chunk in r.iter_content(chunk_size=8192):
                                        f.write(chunk)
                            logging.info(
                                f"Config file {file_name} downloaded.")
                    else:  # For other tools, download the single config file
                        download_url = response.json()['download_url']
                        file_name = os.path.join(
                            tool, repo_name, os.path.basename(config_file))
                        os.makedirs(os.path.dirname(file_name), exist_ok=True)
                        with requests.get(download_url, stream=True) as r:
                            r.raise_for_status()
                            with open(file_name, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        logging.info(f"Config file {file_name} downloaded.")

            # Handle error codes from GitHub API
            elif response.status_code == 403:
                logging.error(
                    f"Permission denied checking for {tool} in {repo_name}. Check your API token.")
                permission_denied = True
                break
            elif response.status_code == 429:
                logging.error(
                    f"Rate limit exceeded checking for {tool} in {repo_name}. Please slow down your requests.")
                break
            elif response.status_code != 404:
                logging.error(
                    f"Error checking for {tool} in {repo_name}: HTTP {response.status_code}")

        # Add the result to the queue
        if permission_denied:
            cicd_tool = "Permission Denied"
        elif detected_tools:
            cicd_tool = ", ".join(detected_tools)
        else:
            cicd_tool = "Unknown"
        row_queue.put([repo_name, cicd_tool])
        logging.info(f"Finished processing of repo: {repo['name']}")
    except Exception as e:
        logging.error(
            f"An error occurred while processing the repo {repo_name}: {str(e)}")

# Function to get information about all repositories of an organization


def get_repo_info(org_name):
    page = 1
    repos = []
    while True:
        url = f"https://api.github.com/orgs/{org_name}/repos?page={page}&per_page=100"
        try:
            response = requests.get(url, headers=headers)
            update_rate_limit(response)
            response_json = response.json()
            if 'message' in response_json:
                if response_json['message'] == "Not Found":
                    logging.error(f"Organization {org_name} not found.")
                elif response_json['message'] == "Forbidden":
                    logging.error("Permission denied. Check your API token.")
                elif response_json['message'] == "You have triggered an abuse detection mechanism. Please wait a few minutes before you try again.":
                    logging.error(
                        "Rate limit exceeded while getting repos. Please slow down your requests.")
                return
            elif response_json:
                repos.extend(response_json)
                page += 1
            else:
                break
        except Exception as e:
            logging.error(
                f"An error occurred while getting the repos: {str(e)}")
            return

    # Process each repository using a ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        for index, repo in enumerate(repos, start=1):
            executor.submit(process_repo, repo, index, len(repos))
            logging.info(
                f"Processing {index} out of {len(repos)} repositories for organization {org_name}. Progress: {index}/{len(repos)}")

    # Write the results to an Excel file
    rows = list(row_queue.queue)
    df = pd.DataFrame(rows, columns=["Repo Name", "CI/CD Tool"])
    df.to_excel(f'{org_name}_{outputfile}', index=False)
    logging.info(f"Output successfully written to {org_name}_{outputfile}")


# Run the script for each organization
for org_name in org_names:
    get_repo_info(org_name)
