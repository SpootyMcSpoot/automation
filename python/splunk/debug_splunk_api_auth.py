import logging
import os
import argparse
from dotenv import load_dotenv
import splunklib.client as client

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load Splunk host, port, and other configuration from environment variables
splunk_host = os.getenv("SPLUNK_HOST")
splunk_port = int(os.getenv("SPLUNK_PORT", "8089"))  # Default to 8089 if not provided
# Load Splunk token from environment variable
token = os.getenv("SPLUNK_TOKEN")

# Load Splunk username and password from environment variables
username = os.getenv("SPLUNK_USERNAME")
password = os.getenv("SPLUNK_PASSWORD")

# Argument parsing
parser = argparse.ArgumentParser(description="Fetch reports from Splunk API")
parser.add_argument("--auth-method", choices=["token", "userpass"], required=True, help="Authentication method: token or userpass")
args = parser.parse_args()

if args.auth_method == "token":
    if token is None:
        logging.error("Splunk token not found in environment variables.")
        exit(1)
elif args.auth_method == "userpass":
    if username is None or password is None:
        logging.error("Splunk username or password not found in environment variables.")
        exit(1)
else:
    logging.error("Invalid authentication method specified.")
    exit(1)

try:
    # Initialize the Splunk service instance
    service = client.connect(
        host=splunk_host,
        port=splunk_port,
        token=token if args.auth_method == "token" else None,
        username=username if args.auth_method == "userpass" else None,
        password=password if args.auth_method == "userpass" else None,
    )

    # Fetch the list of reports
    saved_searches = service.saved_searches.list()

    for saved_search in saved_searches:
        print("Report name:", saved_search.name)

except Exception as e:
    logging.error("An error occurred: %s", e)
