# Import necessary modules
import os
import requests
import json
import jsonschema
import logging
import queue
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set necessary variables
org_names = os.getenv('ORG_NAMES').split(',')  # 'org1,org2' in .env
api_key = os.getenv('GITHUB_API_KEY')
splunk_hec_token = os.getenv('SPLUNK_HEC_TOKEN')
splunk_hec_url = os.getenv('SPLUNK_HEC_URL')
splunk_index = os.getenv('SPLUNK_INDEX')
hec = os.getenv('HEC') == 'True'  # 'True' or 'False' in .env
scope = os.getenv('SCOPE')  # 'org', 'repo', or 'both' in .env
output_file = os.getenv('OUTPUT_FILE')

headers = {
    'Authorization': f'Bearer {api_key}',
    'Accept': 'application/vnd.github+json'
}

headers_splunk = {
    'Authorization': f'Splunk {splunk_hec_token}',
    'Content-Type': 'application/json'
}

# Initialize a queue to store results
org_queue = queue.Queue()
repo_queue = queue.Queue()

# Set up logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("log.txt"),
                        logging.StreamHandler()
                    ])


def perform_request(url, headers, query):
    response = requests.post(url, headers=headers, json={'query': query})

    # Log the entire request object and headers
    logging.info(f"Request Method: {response.request.method}")
    logging.info(f"Request URL: {response.request.url}")
    logging.info(f"Request Headers: {response.request.headers}")
    logging.info(f"Request Body: {response.request.body}")

    # Log response status
    logging.info(f"Response Status Code: {response.status_code}")

    return response


def update_rate_limit(response):
    limit = response.headers.get('X-RateLimit-Limit')
    remaining = response.headers.get('X-RateLimit-Remaining')
    reset_time = response.headers.get('X-RateLimit-Reset')

    logging.info(f"Rate Limit: {limit}")
    logging.info(f"Rate Limit Remaining: {remaining}")
    logging.info(f"Rate Limit Reset Time: {reset_time}")

    if remaining == 0:
        sleep_time = int(reset_time) - time.time()
        logging.info(
            f"Rate limit exceeded. Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)


def get_org_and_repo_info(org_name):
    # Function to get organization and repository information
    logging.info(f"Getting org and repo info for {org_name}")

    # Compressed get_org_info logic
    try:
        org_query = f'''
        query {{
            organization(login: "{org_name}") {{
                name
                login
                url
                description
                createdAt
                updatedAt
                repositories {{ totalCount }}
                membersWithRole(first: 20) {{
                    totalCount
                    edges {{
                        role
                        node {{
                            login
                            name
                            pullRequests(last: 1) {{
                                totalCount
                                nodes {{ createdAt }}
                            }}
                            issues(last: 1) {{
                                totalCount
                                nodes {{ createdAt }}
                            }}
                        }}
                    }}
                }}
                teams(first: 20) {{
                    totalCount
                    edges {{
                        node {{
                            name
                            members {{
                                totalCount
                                edges {{
                                    role
                                    node {{ login name }}
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
        '''

        logging.info(f"Sending request for {org_name}")
        response = perform_request(
            'https://api.github.com/graphql', headers, org_query)
        logging.info(f"Received response for {org_name}")

        update_rate_limit(response)
        if response.status_code == 200:
            org_info = response.json()

            # Log success status
            logging.info(
                f"Successfully fetched org info for {org_name} with status code: {response.status_code}")

            if 'errors' in org_info:
                for error in org_info['errors']:
                    logging.error(
                        f"Error fetching org info for {org_name}: {error['message']}")
                return

            for member_edge in org_info['data']['organization']['membersWithRole']['edges']:
                member = member_edge['node']
                member['lastActivityAt'] = None

                if member['pullRequests']['totalCount'] > 0:
                    pr_time = member['pullRequests']['nodes'][0]['createdAt']
                    member['lastActivityAt'] = pr_time

                if member['issues']['totalCount'] > 0:
                    issue_time = member['issues']['nodes'][0]['createdAt']
                    if member['lastActivityAt'] is None or issue_time > member['lastActivityAt']:
                        member['lastActivityAt'] = issue_time

            org_queue.put(org_info)
            logging.info(
                f"Successfully fetched and queued org info for {org_name}")
        else:
            logging.error(
                f"Error fetching org info for {org_name}: {response.content}")
    except Exception as e:
        logging.error(
            f"Exception occurred while fetching org info for {org_name}: {str(e)}")

    # Compressed get_repo_info logic
    logging.info(f"Getting repo info for {org_name}")
    cursor = None
    all_repos = []

    while True:
        repo_query = f'''
        query {{
            organization(login: "{org_name}") {{
                repositories(first: 50{', after: "' + cursor + '"' if cursor else ''}) {{
                    pageInfo {{ hasNextPage endCursor }}
                    nodes {{
                        name
                        createdAt
                        updatedAt
                        isFork
                        isPrivate
                        primaryLanguage {{ name }}
                        issues {{ totalCount }}
                        pullRequests {{ totalCount }}
                        releases {{ totalCount }}
                        licenseInfo {{ name }}
                        diskUsage
                        commitComments {{ totalCount }}
                        vulnerabilityAlerts {{ totalCount }}
                        forkCount
                        stargazerCount
                        watchers {{ totalCount }}
                        branchProtectionRules(first: 20) {{
                            nodes {{
                                pattern
                                requiresApprovingReviews
                                requiredApprovingReviewCount
                                isAdminEnforced
                            }}
                        }}
                    }}
                }}
            }}
        }}
        '''

        response = perform_request(
            'https://api.github.com/graphql', headers, repo_query)
        update_rate_limit(response)

        if response.status_code == 200:
            repo_info = response.json()

            if 'errors' in repo_info:
                for error in repo_info['errors']:
                    logging.error(
                        f"Error fetching repo info for {org_name}: {error['message']}")
                return

            for repo in repo_info['data']['organization']['repositories']['nodes']:
                repo['organization'] = org_name

            all_repos.extend(
                repo_info['data']['organization']['repositories']['nodes'])

            has_next_page = repo_info['data']['organization']['repositories']['pageInfo']['hasNextPage']
            if has_next_page:
                cursor = repo_info['data']['organization']['repositories']['pageInfo']['endCursor']
                time.sleep(0.5)
            else:
                break
        else:
            logging.error(
                f"Error fetching repo info for {org_name}: {response.content}")
            break

    all_repos_dict = {
        'data': {
            'organization': {
                'repositories': {
                    'nodes': all_repos
                }
            }
        }
    }

    repo_queue.put(all_repos_dict)
    logging.info(f"Successfully fetched and queued repo info for {org_name}")


def transform_to_splunk_format(data, scope_type):
    return {
        "time": int(time.time()),
        "host": "github",
        "source": "github",
        "sourcetype": f'github:{scope_type}',
        "index": splunk_index,
        "event": data
    }


def validate_event(event):
    schema = {
        "type": "object",
        "properties": {
            "time": {"type": "number"},
            "host": {"type": "string"},
            "source": {"type": "string"},
            "sourcetype": {"type": "string"},
            "index": {"type": "string"},
            "event": {"type": "object"},
        },
        "required": ["event"],
    }

    try:
        jsonschema.validate(instance=event, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        logging.error(f"Event validation error: {str(e)}")
        return False


def save_to_splunk(data, splunk_url, token, index, scope_type):
    # Transform and validate the data payload for Splunk
    event_data = transform_to_splunk_format(data, scope_type)
    if not validate_event(event_data):
        logging.error(f"Invalid event data: {event_data}")
        return

    # Log the entire PUT request
    put_request = {
        "url": f"{splunk_url}/services/collector/event",
        "headers": headers_splunk,
        "data": json.dumps(event_data)
    }
    logging.info(f"Sending the following PUT request to Splunk: {put_request}")

    # Send the data to Splunk using the requests library
    response = requests.post(
        put_request["url"], headers=put_request["headers"], data=put_request["data"])
    if response.status_code == 200:
        logging.info(
            f"Successfully posted {scope_type} data to Splunk with status code: {response.status_code}")
    else:
        logging.error(
            f"Failed to post {scope_type} data to Splunk. Response status code: {response.status_code}")
        logging.error(f"Response content: {response.content}")


# Define the executor
with ThreadPoolExecutor(max_workers=5) as executor:
    org_futures = {executor.submit(get_org_and_repo_info, org_name)
                   for org_name in org_names}

while not org_queue.empty() or not repo_queue.empty():
    if not org_queue.empty() and scope in ['org', 'both']:
        org_info = org_queue.get()
        if hec:
            save_to_splunk(org_info, splunk_hec_url,
                           splunk_hec_token, splunk_index, 'organization')
        else:
            with open(output_file, 'a') as f:
                json.dump(org_info, f, indent=4)
                f.write('\n')
                logging.info("Successfully wrote org data to file")

    if not repo_queue.empty() and scope in ['repo', 'both']:
        repo_info = repo_queue.get()
        if hec:
            save_to_splunk(repo_info, splunk_hec_url,
                           splunk_hec_token, splunk_index, 'repository')
        else:
            with open(output_file, 'a') as f:
                json.dump(repo_info, f, indent=4)
                f.write('\n')
                logging.info("Successfully wrote repo data to file")
