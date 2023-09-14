from github import Github, GithubException
import logging
import csv
from datetime import datetime, timedelta

# Configuration and Variables
access_token = ""
organizations = [""]
csv_file = 'active_users.csv'

# Initialize Github object
g = Github(access_token)

# Logging Configuration
logging.basicConfig(filename='github_query.log', level=logging.INFO)
logging.info("Script started")


def fetch_users_who_committed(org_name):
    logging.info(f"Fetching repositories for organization: {org_name}")
    org = g.get_organization(org_name)
    active_users = {}
    sixty_days_ago = datetime.utcnow() - timedelta(days=60)

    repo_count = 0
    for repo in org.get_repos():
        repo_count += 1
        logging.info(
            f"Fetching data for repository: {repo.name} (Repo {repo_count})")

        try:
            commit_count = 0
            for commit in repo.get_commits(since=sixty_days_ago):
                commit_count += 1
                try:
                    username = commit.author.login
                    if username not in active_users:
                        active_users[username] = 0
                    active_users[username] += 1
                except AttributeError:  # If commit.author is None
                    continue
            logging.info(
                f"Processed {commit_count} commits in repo: {repo.name}")

        except GithubException as e:
            logging.warning(
                f"Skipping repository {repo.name} due to GitHub exception: {e}")
            continue

    logging.info(
        f"Finished processing repositories for organization: {org_name}")
    return active_users


# Main Logic
with open(csv_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Organization', 'Username', 'Commit Count'])

    org_count = 0
    for org in organizations:
        org_count += 1
        logging.info(f"Processing organization: {org} (Org {org_count})")

        active_users = fetch_users_who_committed(org)

        logging.info(
            f"Found {len(active_users)} active users for organization: {org}")
        print(
            f"Organization: {org}, Users who committed in last 60 days: {len(active_users)}")

        for username, commit_count in active_users.items():
            logging.info(f"Writing data for user: {username}")
            print(f"Username: {username}, Commit Count: {commit_count}")
            writer.writerow([org, username, commit_count])

        logging.info(f"Finished processing organization: {org}")

logging.info("Script completed")
