import requests
import csv
import re
import os
from dotenv import load_dotenv

# Set variables
load_dotenv()  # take environment variables from .env
splunk_host = "<your-splunk-instance>"
splunk_username = os.getenv('username')
splunk_password = os.getenv('password')
splunk_app = "<your-app>"

# API endpoints
reports_endpoint = f"https://{splunk_host}/servicesNS/{splunk_username}/{splunk_app}/saved/searches"
results_endpoint = f"https://{splunk_host}/servicesNS/{splunk_username}/{splunk_app}/saved/searches/{}/results"

# Authentication
auth = (splunk_username, splunk_password)

# Function to extract sub-values from the title
def extract_sub_values(title):
    sub_values = {}
    patterns = {
        "Creator": r"Creator\n(.*?)\n",
        "App": r"App\n(.*?)\n",
        "Schedule": r"Schedule\n(.*?)\n",
        "Actions": r"Actions\n(.*?)\n",
        "Acceleration": r"Acceleration\n(.*?)\n",
        "Permissions": r"Permissions\n(.*?)\n",
        "Modified": r"Modified\n(.*?)\n",
        "Embedding": r"Embedding\n(.*?)\n"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, title)
        sub_values[key] = match.group(1) if match else ""

    return sub_values

# Retrieve the list of reports
response = requests.get(reports_endpoint, auth=auth)
reports = response.json()["entry"]

# Extract and store report data in a CSV file
with open("splunk_reports.csv", "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Report Name", "Creator", "App", "Schedule", "Actions", "Acceleration", "Permissions", "Modified", "Embedding"])

    for report in reports:
        report_id = report["name"]
        report_title = report["content"]["title"]

        results_response = requests.get(results_endpoint.format(report_id), auth=auth)
        results = results_response.json()["results"]

        sub_values = extract_sub_values(report_title)

        writer.writerow([report_title, sub_values["Creator"], sub_values["App"], sub_values["Schedule"],
                         sub_values["Actions"], sub_values["Acceleration"], sub_values["Permissions"],
                         sub_values["Modified"], sub_values["Embedding"]])

print("Reports extracted and saved successfully.")
