import os
import logging
from github import Github

# Provide your personal access token
token = ''
# Provide your output directory
output_dir = '/mnt/z/repo_dump'  # Default directory, change as needed


def clone_repos_with_commits(token, output_dir):
    # Ensure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        format='[%(levelname)s] %(message)s')

    # Authenticate with GitHub using a personal access token
    g = Github(token)

    # Search for public repositories (this will only get a fraction of them)
    repositories = g.search_repositories('is:public')

    # Iterate over found repositories
    for repo in repositories:
        # Check if the repository has more than 10 commits
        if repo.get_commits().totalCount > 10:
            logging.info(f"Cloning repository: {repo.name}")

            # Clone the repository to the specified directory
            os.system(
                f'git clone {repo.clone_url} {os.path.join(output_dir, repo.name)}')


# Call the function to clone the repositories
clone_repos_with_commits(token, output_dir)
