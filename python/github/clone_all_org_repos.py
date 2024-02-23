import requests
import os
import logging
import argparse
from dotenv import load_dotenv
import git

# Load environment variables from .env file
load_dotenv()

# Configuration settings
github_api_url = "https://api.github.com"
org_name = ''
github_token = os.getenv('github_token')
output_dir = "./repos"
timeout = 10  # Constant for network request timeout

# Set up logging with desired format
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def fetch_repos(org_name, page):
    """
    Fetch the repositories for the given organization and page number.
    """
    headers = {
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    response = requests.get(
        f"{github_api_url}/orgs/{org_name}/repos?page={page}&per_page=100",
        headers=headers,
        timeout=timeout
    )

    if response.status_code != 200:
        response.raise_for_status()

    return response.json()


def clone_all_repos(output_dir, org_name):
    """
    Clone all repositories of the specified organization.
    """
    page = 1
    total_repos = 0
    cloned_repos = 0
    failed_repos = 0

    while True:
        try:
            repos = fetch_repos(org_name, page)
        except requests.RequestException as e:
            logging.error(f"Failed to fetch repos. Error: {e}")
            break

        if not repos:
            break

        for repo in repos:
            repo_url = repo["clone_url"]
            repo_name = repo["name"]
            dest = os.path.join(output_dir, repo_name)
            try:
                git.Repo.clone_from(repo_url, dest)
                cloned_repos += 1
            except git.GitCommandError as e:
                failed_repos += 1
                logging.error(f"Failed to clone {repo_name}. Error: {e}")

        total_repos += len(repos)
        page += 1

    logging.info(
        f"Total repositories: {total_repos}. Cloned: {cloned_repos}. Failed: {failed_repos}")


def setup_and_run_cloning():
    """
    Setup and run the cloning process.
    """
    parser = argparse.ArgumentParser(
        description="Clone all repos from a GitHub org.")
    parser.add_argument("--output", default=output_dir,
                        help="Output directory for cloned repos")
    args = parser.parse_args()

    if not all([org_name, github_token]):
        logging.error(
            "Please set org_name and github_token environment variables.")
        return

    if not os.path.exists(args.output):
        os.makedirs(args.output)

    clone_all_repos(args.output, org_name)


setup_and_run_cloning()
