import csv
import requests


def get_all_commits(repo_owner, repo_name, headers):
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
    commits = []
    page = 1
    while True:
        params = {"page": page, "per_page": 100}
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code == 200:
            page_commits = response.json()
            if len(page_commits) > 0:
                commits.extend(page_commits)
                page += 1
            else:
                break
        else:
            print(
                f"Error: {response.status_code} - {response.json()['message']}")
            break
    return commits


def retrieve_commits_to_csv(repo_list, csv_file_path, headers):
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Repository", "Commit SHA", "Commit Message",
                        "Commit Branch", "Commit Date", "Commit Owner"])
        for repo in repo_list:
            repo_owner, repo_name = repo['owner'], repo['name']
            commits = get_all_commits(repo_owner, repo_name, headers)
            for commit in commits:
                commit_sha = commit['sha']
                commit_message = commit['commit']['message']
                commit_branch = commit['commit']['tree']['sha']
                commit_date = commit['commit']['committer']['date']
                commit_owner = commit['commit']['author']['name']
                writer.writerow([f"{repo_owner}/{repo_name}", commit_sha,
                                commit_message, commit_branch, commit_date, commit_owner])


# Example usage:
repo_list = [
    {'owner': 'hashicorp', 'name': 'terraform-provider-aws'}
]

api_key = "MY_API_KEY_HERE"
headers = {
    "Authorization": f"Bearer {api_key}"
}

csv_file_path = "commits.csv"

retrieve_commits_to_csv(repo_list, csv_file_path, headers)

print("Commits retrieved and saved to commits.csv")
