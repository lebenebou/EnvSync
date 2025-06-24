
import settings

import requests
import re

import sys
import argparse

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class IssueInfo:

    issueKeyPattern: str = r'\w+-\d+'

    def __init__(self, data: dict):
        
        self.id: str = data.get('key')
        self.defect: str = data.get('fields', {}).get('customfield_11369')

        self.assignee: str = data.get('fields', {}).get('assignee', {}).get('name')

        self.summary: str = data.get('fields', {}).get('summary')

    def toPerforceDescription(self, withId: bool = False, revert: bool = False) -> str:

        description: str = ''
        description += f'[{self.defect}]'

        if revert:
            description += '[REVERT]'

        if withId:
            description += f'[{self.id}]'

        if not self.summary.startswith('['):
            description += ' '

        description += self.summary
        return description

    def __str__(self) -> str:
        return self.toPerforceDescription(withId=True)

class JiraRequestHandler:

    @staticmethod
    def buildDefaultHeaders() -> dict:

        token = settings.getJiraApiToken()

        if not token:
            print(f'Jira API token not found. Please set it in your settings JSON file as "jira_token"', file=sys.stderr)
            return {}

        return {'Authorization': f'Bearer {settings.getJiraApiToken()}', 'Accept': 'application/json'}

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
    def fetchDeveloperIssues(assignee: str, maxResults: int = 20, searchTerm: str = None) -> list[IssueInfo]:

        jqlStatement: str = f"assignee={assignee} AND cf[11369] IS NOT EMPTY"

        if searchTerm:
            searchTerm.strip('*')
            searchTerm = '*' + searchTerm + '*'
            jqlStatement += f" AND summary ~ \"{searchTerm}\""

        if True:
            jqlStatement += f" ORDER BY created DESC"

        message: str = f'Fetching Jira issues assigned to {assignee}... (limiting search to {maxResults}'
        if searchTerm:
            message += f' and looking for "{searchTerm}"'

        message += ')'
        print(message, file=sys.stderr)

        endpoint: str = 'https://mxjira.murex.com/rest/api/latest/search'

        filterParams = {
            "jql" : jqlStatement,
            "maxResults" : maxResults,
        }
        response = JiraRequestHandler.getRequest(endpoint, params=filterParams)
        
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

        filterParams = {
            "jql" : f"cf[11369]={defect}",
            "maxResults" : 1,
        }
        response = JiraRequestHandler.getRequest(endpoint, params=filterParams)
        
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

        m = re.match(r'DEF\d+', issueIdOrDefect)
        if m:
            return JiraRequestHandler._fetchIssueInfoByDefect(m.group())

        issueId: str = issueIdOrDefect.split('/')[-1]
        m = re.match(IssueInfo.issueKeyPattern, issueId)
        if m:
            return JiraRequestHandler._fetchIssueInfoById(m.group())

        print(f'Not an Jira issue ID or Defect: {issueIdOrDefect}', file=sys.stderr)
        return None

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Helper for Jira points')
    parser.add_argument('--id', default=None, type=str, help='Jira ID or Defect ID', required=False)
    parser.add_argument('-m', '--max-results', default=20, type=int, help='limit the output to a certain number of jira issues')
    parser.add_argument('-s', '--search', default=None, type=str, help='filter on points with this substring in the summary')

    args, _ = parser.parse_known_args()

    parsedId: str = args.id
    if parsedId:

        issue = JiraRequestHandler.fetchIssueInfo(parsedId)
        if not issue:
            print(f'Issue not found: {parsedId}', file=sys.stderr)
            exit(1)

        print(issue)
        exit(0)

    from SessionInfo import SessionInfo
    session = SessionInfo()
    issues: list[IssueInfo] = JiraRequestHandler.fetchDeveloperIssues(session.username, maxResults=args.max_results, searchTerm=args.search)
    for issue in issues:
        print(issue)

    exit(0)