import requests
import os
import subprocess
import logging
import argparse

# Configuration
GITHUB_API_URL = "https://api.github.com"
ORG_NAME = "your_org_name_here"  # Replace with the organization's name
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"  # Replace with your personal access token
# Default output directory; can be overridden by arg
OUTPUT_DIR = "output_directory"

# Setup logging
logging.basicConfig(level=logging.INFO)


def clone_all_repos(output_dir):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    page = 1

    # Loop to handle pagination from GitHub API
    while True:
        response = requests.get(
            f"{GITHUB_API_URL}/orgs/{ORG_NAME}/repos?page={page}&per_page=100",
            headers=headers,
        )

        if response.status_code != 200:
            logging.error(
                f"Failed to fetch repositories with status code: {response.status_code}")
            return

        repos = response.json()

        # Break out of loop if there are no more repos to process
        if not repos:
            break

        for repo in repos:
            repo_url = repo["clone_url"]
            repo_name = repo["name"]
            dest = os.path.join(output_dir, repo_name)

            logging.info(f"Cloning {repo_name}...")
            try:
                subprocess.run(["git", "clone", repo_url, dest], check=True)
                logging.info(f"Cloned {repo_name} successfully to {dest}")
            except subprocess.CalledProcessError:
                logging.error(f"Failed to clone {repo_name}")

        # Move to the next page
        page += 1


parser = argparse.ArgumentParser(
    description="Clone all repos from a GitHub org.")
parser.add_argument("--output", default=OUTPUT_DIR,
                    help="Output directory for cloned repos")
args = parser.parse_args()

if not os.path.exists(args.output):
    os.makedirs(args.output)

clone_all_repos(args.output)
