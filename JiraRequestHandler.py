
import settings
import SessionInfo

import re
import json

import requests
from typing import List, Dict

import sys

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from enum import Enum

import base64
def tryDecrypt(encoded_message: str) -> str | None:

    if not encoded_message:
        return None

    try:
        base64_bytes = encoded_message.encode('utf-8')
        message_bytes = base64.b64decode(base64_bytes, validate=True)
        return message_bytes.decode('utf-8')

    except (ValueError, UnicodeDecodeError):
        return None

class IssueInfo:

    def __init__(self, data: dict):
        
        self.id = data.get('key')
        self.defect = data.get('fields', {}).get('customfield_11369')

        self.summary = data.get('fields', {}).get('summary')

class JiraRequestHandler:

    @staticmethod
    def buildDefaultHeaders() -> dict:

        token = settings.getJiraApiToken()

        if not token:
            print(f'Jira API token not found. Please set it in your settings JSON file as "jira_token"', file=sys.stderr)
            return {}

        return {'Authorization': f'Bearer {settings.getJiraApiToken()}', 'Accept': 'application/json'}

    @staticmethod
    def buildDefectSearchParams(defect: str) -> dict:

        return {
            "fields" : "id,key,fiels",
            "maxResults" : 1,

            "jql" : f"cf[11369]={defect}",
        }

    @staticmethod
    def getRequest(endpoint: str, params: dict = None) -> requests.Response:
        
        response = None
        try:
            response = requests.get(endpoint, headers=JiraRequestHandler.buildDefaultHeaders(),
                                    params=params,
                                    verify=False)

        except requests.exceptions.ConnectionError:
                print(f'\nCould not reach Jira endpoint: {endpoint}', file=sys.stderr)
                print('Make sure you are connected to the internet.', file=sys.stderr)
                print('If you are not on Murex premises, make sure you\'re connected through a VPN.', file=sys.stderr)
                exit(2)

        if response.status_code == 401:

            print('Wrong username or password. Authentication failed', file=sys.stderr)
            return None

        if response.status_code == 404:

            print(f'Not found: {endpoint}', file=sys.stderr)
            return None

        if response.status_code != 200:

            print(f'Error occured in GET request:\n{response.text}', file=sys.stderr)
            return None

        return response

    @staticmethod
    def fetchIssueIdFromDefect(defect: str):

        response = JiraRequestHandler.getRequest('https://mxjira.murex.com/rest/api/latest/search', params=JiraRequestHandler.buildDefectSearchParams(defect))
        
        if not response:
            return None

        issues: list[dict] = response.json().get('issues')

        if not len(issues):
            print(f'No Jira issues were found with defect: {defect}', file=sys.stderr)
            return None

        issueEndpoint = issues[0].get('key')
        return issueEndpoint

    @staticmethod
    def fetchIssueInfo(issueId: str) -> IssueInfo:

        endpoint: str = 'https://mxjira.murex.com/rest/api/latest/issue/'
        issueId = issueId.strip('/').strip(endpoint)
        endpoint += issueId

        response = JiraRequestHandler.getRequest(endpoint)

        if not response:
            print(f'Failed to fetch Jira issue: {issueId}', file=sys.stderr)
            return None

        data: dict = response.json()
        return IssueInfo(data)

    @staticmethod
    def fetchIssueInfoByDefect(defect: str) -> IssueInfo:

        issueId: str = JiraRequestHandler.fetchIssueIdFromDefect(defect)

        if not issueId:
            return None

        issue: IssueInfo = JiraRequestHandler.fetchIssueInfo(issueId)
        return issue
        
if __name__ == '__main__':

    # example usage

    issue = JiraRequestHandler.fetchIssueInfo('LIEDI-9903')
    print(issue.defect)