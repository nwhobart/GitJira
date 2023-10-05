#!/usr/bin/env python3

import os
import sys
import re
import logging
from git import Repo
from jira import JIRA

# Set up logging
logging.basicConfig(level=logging.INFO)

def get_branch_name_based_on_jira_ticket(jira_server, jira_email, jira_api_token, ticket_id):
    # Ensure the ticket ID has a prefix before proceeding
    if '-' not in ticket_id:
        logging.error("Ticket ID must include a prefix followed by a hyphen.")
        exit(1)

    jira = JIRA(server=jira_server, basic_auth=(jira_email, jira_api_token))
    ticket = jira.issue(ticket_id)

    issue_type = ticket.fields.issuetype.name.lower()
    branch_prefix = "feature" if issue_type == "story" else "fix" if issue_type == "bug" else "issue"

    branch_name = f"{branch_prefix}/{ticket_id}-{ticket.fields.summary.replace(' ', '_').replace('/', '').replace(':', '').replace('?', '').lower()}"

    # Ensure the branch name doesn't exceed 100 characters
    if len(branch_name) > 100:
        branch_name = branch_name[:100]

    return branch_name

def create_git_branch_and_set_upstream(branch_name):
    repo = Repo()

    if repo.is_dirty():
        logging.info("Please commit your changes before creating a new branch.")
        return

    origin = repo.remotes.origin
    logging.info("Pulling the latest changes from the remote repository...")
    origin.pull()
    logging.info("Successfully pulled the latest changes.")

    logging.info(f"Creating new branch '{branch_name}'...")
    repo.create_head(branch_name)
    logging.info(f"Successfully created new branch '{branch_name}'.")

    logging.info(f"Checking out to the new branch '{branch_name}'...")
    repo.heads[branch_name].checkout()
    logging.info(f"Successfully checked out to '{branch_name}'.")

    logging.info(f"Pushing the new branch '{branch_name}' and setting the upstream...")
    origin.push(branch_name, set_upstream=True)
    logging.info(f"Successfully pushed the new branch '{branch_name}' and set the upstream.")

if __name__ == "__main__":
    jira_server = os.environ.get('JIRA_SERVER', 'https://clearcover.atlassian.net/')
    jira_email = os.environ.get('JIRA_EMAIL')
    jira_api_token = os.environ.get('JIRA_API_TOKEN')

    if not jira_email or not jira_api_token:
        logging.error("JIRA_EMAIL and JIRA_API_TOKEN environment variables must be set.")
        exit(1)

    # Check for a command-line argument (JIRA ticket ID)
    if len(sys.argv) == 2 and re.match(r"([A-Z]+-)?\d+", sys.argv[1]):
        ticket_id = sys.argv[1]
    else:
        ticket_id = input("Enter the JIRA ticket ID (with the prefix, e.g., 'SRE-1234'): ")

    if not re.match(r"([A-Z]+-)?\d+", ticket_id):
        logging.error("Invalid ticket ID format.")
        exit(1)

    branch_name = get_branch_name_based_on_jira_ticket(jira_server, jira_email, jira_api_token, ticket_id)
    create_git_branch_and_set_upstream(branch_name)
