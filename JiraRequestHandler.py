
import settings

import requests
import re

from p4Helper import P4Helper

import sys

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class IssueInfo:

    issueKeyPattern: str = r'\w+-\d+'

    def __init__(self, data: dict):
        
        self.id: str = data.get('key')
        self.defect: str = data.get('fields', {}).get('customfield_11369')

        self.assignee: str = data.get('fields', {}).get('assignee', {}).get('name')

        self.summary: str = data.get('fields', {}).get('summary')

class JiraRequestHandler:

    @staticmethod
    def buildDefaultHeaders() -> dict:

        token = settings.getJiraApiToken()

        if not token:
            print(f'Jira API token not found. Please set it in your settings JSON file as "jira_token"', file=sys.stderr)
            return {}

        return {'Authorization': f'Bearer {settings.getJiraApiToken()}', 'Accept': 'application/json'}

    @staticmethod
    def buildDefectFilterParams(defect: str) -> dict:

        return {
            "jql" : f"cf[11369]={defect}",
            "maxResults" : 1,
        }

    @staticmethod
    def buildAssigneeFilterParams(user: str, maxResults: int = 20) -> dict:

        return {
            "jql" : f"assignee={user}",
            "maxResults" : maxResults,
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
    def fetchUsersIssues(assignee: str, maxResults: int = 20) -> list[IssueInfo]:

        print(f'Fetching Jira issues assigned to {assignee}... (limiting search to {maxResults})', file=sys.stderr)

        endpoint: str = 'https://mxjira.murex.com/rest/api/latest/search'
        response = JiraRequestHandler.getRequest(endpoint, params=JiraRequestHandler.buildAssigneeFilterParams(user=assignee, maxResults=maxResults))
        
        if not response:
            return None

        issues: list[dict] = response.json().get('issues')

        if not len(issues):
            print(f'No Jira issues were found assigned to: {assignee}', file=sys.stderr)
            return []

        return [IssueInfo(issue) for issue in issues]

    @staticmethod
    def _fetchIssueInfoByDefect(defect: str) -> IssueInfo:

        print(f'Looking for Jira issue with defect: {defect}...', file=sys.stderr)

        endpoint: str = 'https://mxjira.murex.com/rest/api/latest/search'
        response = JiraRequestHandler.getRequest(endpoint, params=JiraRequestHandler.buildDefectFilterParams(defect))
        
        if not response:
            return None

        issues: list[dict] = response.json().get('issues')

        if not len(issues):
            print(f'No Jira issues were found with defect: {defect}', file=sys.stderr)
            return None

        issue = issues[0]
        return IssueInfo(issue)

    @staticmethod
    def _fetchIssueInfoById(issueId: str) -> IssueInfo:

        assert re.match(IssueInfo.issueKeyPattern, issueId), f'{issueId} is not a Jira issue string'

        endpoint: str = 'https://mxjira.murex.com/rest/api/latest/issue/'
        issueId = issueId.strip('/').strip(endpoint)
        endpoint += issueId

        print(f'Fetching Jira issue: {issueId}...', file=sys.stderr)
        response = JiraRequestHandler.getRequest(endpoint)

        if not response:
            print(f'Failed to fetch Jira issue: {issueId}', file=sys.stderr)
            return None

        data: dict = response.json()
        return IssueInfo(data)

    @staticmethod
    def fetchIssueInfo(issueIdOrDefect: str) -> IssueInfo:

        m = re.match(P4Helper.DefectRegex, issueIdOrDefect)
        if m:
            return JiraRequestHandler._fetchIssueInfoByDefect(m.group())

        issueId: str = issueIdOrDefect.split('/')[-1]
        m = re.match(IssueInfo.issueKeyPattern, issueId)
        if m:
            return JiraRequestHandler._fetchIssueInfoById(m.group())

        print(f'Not an Jira issue ID or Defect: {issueIdOrDefect}', file=sys.stderr)
        return None

if __name__ == '__main__':

    # example usage

    for jiraIssue in JiraRequestHandler.fetchUsersIssues('yoyammine', 100):

        print(jiraIssue.__dict__, end='\n\n')