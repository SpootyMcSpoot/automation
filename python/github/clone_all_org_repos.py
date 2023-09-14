import requests
import os
import subprocess
import logging
import argparse

# Configuration
GITHUB_API_URL = "https://api.github.com"
ORG_NAME = ""  # Replace with the organization's name
# Replace with your personal access token
GITHUB_TOKEN = ""
# Default output directory; can be overridden by arg
OUTPUT_DIR = ""

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def clone_all_repos(output_dir):
    if not GITHUB_TOKEN:
        logging.error(
            "GitHub token is not set. Please configure the GITHUB_TOKEN variable.")
        return

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    page = 1
    total_repos = 0
    cloned_repos = 0
    failed_repos = 0

    # Loop to handle pagination from GitHub API
    while True:
        logging.info(f"Fetching repositories for {ORG_NAME} on page {page}...")
        try:
            response = requests.get(
                f"{GITHUB_API_URL}/orgs/{ORG_NAME}/repos?page={page}&per_page=100",
                headers=headers,
            )
        except requests.RequestException as e:
            logging.error(f"Request to GitHub API failed. Error: {e}")
            return

        if response.status_code != 200:
            logging.error(
                f"Failed to fetch repositories with status code: {response.status_code}. Reason: {response.text}")
            return

        repos = response.json()

        if not repos:
            logging.info(
                f"Finished processing all pages. Total repositories: {total_repos}.")
            logging.info(
                f"Successfully cloned: {cloned_repos}. Failed to clone: {failed_repos}.")
            break

        total_repos += len(repos)
        logging.info(f"Retrieved {len(repos)} repositories from page {page}.")

        for repo in repos:
            repo_url = repo["clone_url"]
            repo_name = repo["name"]
            dest = os.path.join(output_dir, repo_name)

            logging.info(f"Cloning {repo_name}...")
            try:
                subprocess.run(["git", "clone", repo_url, dest], check=True)
                logging.info(f"Cloned {repo_name} successfully to {dest}")
                cloned_repos += 1
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to clone {repo_name}. Error: {e}")
                failed_repos += 1
            except Exception as e:
                logging.error(
                    f"Unexpected error occurred while cloning {repo_name}. Error: {e}")

        # Move to the next page
        page += 1


parser = argparse.ArgumentParser(
    description="Clone all repos from a GitHub org.")
parser.add_argument("--output", default=OUTPUT_DIR,
                    help="Output directory for cloned repos")
args = parser.parse_args()

try:
    if not os.path.exists(args.output):
        os.makedirs(args.output)
except Exception as e:
    logging.error(
        f"Failed to create output directory {args.output}. Error: {e}")

clone_all_repos(args.output)
