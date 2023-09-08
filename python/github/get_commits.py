import requests

def get_all_commits(repo_owner, repo_name):
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
    response = requests.get(api_url)
    if response.status_code == 200:
        commits = response.json()
        return commits
    else:
        print(f"Error: {response.status_code} - {response.json()['message']}")
        return []

def get_all_commits_from_repos(repos):
    all_commits = []
    for repo in repos:
        commits = get_all_commits(repo['owner'], repo['name'])
        all_commits.extend(commits)
    return all_commits

# Example usage:
repos = [
    {'owner': 'owner1', 'name': 'repo1'},
    {'owner': 'owner2', 'name': 'repo2'},
    {'owner': 'owner3', 'name': 'repo3'}
]

all_commits = get_all_commits_from_repos(repos)

# Print commit information
for commit in all_commits:
    print(f"Commit SHA: {commit['sha']}")
    print(f"Commit Message: {commit['commit']['message']}")
    print("------")
