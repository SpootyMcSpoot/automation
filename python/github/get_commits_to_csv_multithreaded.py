import requests
import pandas as pd
import threading

API_KEY = "MY_API_KEY"

ORG_NAME = "MY_ORG_NAME"


def get_repo_list():
    url = f"https://api.github.com/orgs/{ORG_NAME}/repos"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        repos = response.json()

        repo_list = []
        for repo in repos:
            repo_list.append({"owner": ORG_NAME, "name": repo["name"]})

        return repo_list

    except requests.exceptions.RequestException as e:
        print(
            f"Error retrieving repository list for organization {ORG_NAME}: {e}")

    return []


def get_commit_history(repo_owner, repo_name, commit_data):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/commits"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        page = 1
        while True:
            params = {
                "page": page,
                "per_page": 100
            }
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            commits = response.json()

            if not commits:
                break

            for commit in commits:
                commit_sha = commit["sha"]

                commit_data.append({
                    "Repo Name": f"{repo_owner}/{repo_name}",
                    "Commit": commit_sha,
                    "Commit Message": commit["commit"]["message"],
                    "Commit Date": commit["commit"]["committer"]["date"],
                    "Commit Owner": commit["commit"]["committer"]["name"]
                })

            page += 1

    except requests.exceptions.RequestException as e:
        print(
            f"Error retrieving commit history for {repo_owner}/{repo_name}: {e}")


def retrieve_commit_history(repo_list):
    commit_data = []
    lock = threading.Lock()

    def thread_task(repo):
        print(
            f"Retrieving commit history for {repo['owner']}/{repo['name']}...")
        repo_commit_data = []
        get_commit_history(repo["owner"], repo["name"], repo_commit_data)

        with lock:
            commit_data.extend(repo_commit_data)

        print(
            f"Completed commit history retrieval for {repo['owner']}/{repo['name']}.")

    threads = []
    for repo in repo_list:
        thread = threading.Thread(target=thread_task, args=(repo,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    df = pd.DataFrame(commit_data)
    df.to_csv("commit_history.csv", index=False)
    print("Commit history saved to commit_history.csv")


# Get the repository list for the organization
repo_list = get_repo_list()

# Retrieve commit history for the repositories
retrieve_commit_history(repo_list)
