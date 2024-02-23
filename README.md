# Python Utilities Collection

This repository contains a diverse collection of Python scripts designed for various purposes, ranging from financial analysis to GitHub repository management, web scraping, and more. Each script serves a unique function and is organized into directories based on their application domain.

## Directory Structure and Descriptions

### Finance
- `yahoo_finance_correlations.py`: A proof of concept (POC) rough draft script for analyzing correlations using Yahoo Finance data.

### GitHub
- `clone_all_org_repos.py`: Script to clone all repositories of a specific organization.
- `clone_all_public_github_repos.py`: A POC rough draft for cloning all public repositories from GitHub.
- `get_active_commiters.py`: Utility to extract active committers of a repository and export the data to a CSV file.
- `get_commits_to_csv_multithreaded.py`: Fetches commits on the main branch for each repository in an organization using multithreading, and exports the data to CSV.
- `get_commits_to_csv.py`: A parallel logic POC rough draft for fetching commits on the main branch per repository in an organization and exporting to CSV (non-multithreaded).
- `repo_cicd_tool_by_org.py`: Identifies the CI/CD tool used in each repository within an organization by checking for well-known CI/CD configuration files and writes the findings to a CSV file.

### Misc
- `getwellsoon.py`: A simple script that generates a 'Get Well Soon' message output.

### Scraping
- `commercial_web_scraping.py`: Designed for scraping videos from websites like retrojunk.com and archive.org. 
  - **Disclaimer**: This script is provided for informational purposes only. I am not liable for how it is used.

### SoundCloud
- `soundcloud_playlist_downloader.py`: Downloads playlists and profile songs from SoundCloud.
  - **Disclaimer**: This script is provided for informational purposes only. I am not liable for how it is used.

### Splunk
- `debug_splunk_api_auth.py`: Assists in debugging API permission issues when provisioning new user access to various Splunk API endpoints.
- `splunk_github_security_auditing.py`: Gathers relevant information on GitHub organizations, teams, and repositories. It parses this information and pushes them to Splunk's HTTP Event Collector (HEC) endpoint for event creation.
- `splunk_reports_to_csv.py`: Audits reports on a Splunk instance via API, parses the information, and writes it to a CSV file.

## Usage and Contributions

Each script in this repository is intended for specific use cases. Users are encouraged to refer to individual script documentation for detailed instructions on usage and customization.

Contributions to the repository, in the form of improvements, bug fixes, or new utility scripts, are welcome. Please adhere to standard coding practices and provide documentation for any new submissions.

## License and Liability

Unless otherwise specified, the scripts in this repository are released under the [MIT License](LICENSE). This ensures free usage and distribution with proper attribution.

**Liability Disclaimer**: The author of this repository is not liable for any misuse of the scripts contained herein. Users are responsible for ensuring that their use of these scripts complies with all relevant legal and ethical standards.
