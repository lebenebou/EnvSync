
import settings

import requests
import re

from SessionInfo import SessionInfo
from p4Helper import P4Helper, Changelist

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

    def toPerforceDescription(self, withId: bool = False, revert: bool = False) -> str:

        description: str = ''
        description += f'[{self.defect}]'

        if revert:
            description += '[REVERT]'

        if withId:
            description += f'[{self.id}]'

        description += ' '
        description += self.summary
        return description

    def __str__(self) -> str:
        return self.toPerforceDescription()

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
    def fetchDeveloperIssues(assignee: str, maxResults: int = 20) -> list[IssueInfo]:

        print(f'Fetching Jira issues assigned to {assignee}... (limiting search to {maxResults})', file=sys.stderr)

        endpoint: str = 'https://mxjira.murex.com/rest/api/latest/search'

        filterParams = {
            "jql" : f"assignee={assignee} AND cf[11369] IS NOT EMPTY ORDER BY created DESC",
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
    def fetchLatestUnsubmittedIssue(assignee: str, version: str, verbose: bool = False) -> IssueInfo:

        # based on if the defect of the issue is found on the version
        latestIssues: list[IssueInfo] = JiraRequestHandler.fetchDeveloperIssues(assignee, 20)
        versionCls: list[Changelist] = P4Helper.getChangelists(version, developer=assignee)
        buildCls: list[Changelist] = P4Helper.getChangelists(P4Helper.Build, developer=assignee)

        if verbose:
            print(f'Filering out submitted defects...', file=sys.stderr)
        submittedDefects: set[str] = set([cl.defect for cl in versionCls])
        submittedDefects.update(cl.defect for cl in buildCls)

        for issue in latestIssues:

            if issue.defect not in submittedDefects:
                print('[FOUND]', issue, file=sys.stderr)
                return issue

            if verbose:
                print('[ALREADY SUBMITTED]', issue, file=sys.stderr)

        return None

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

    session = SessionInfo(forceVerbose=True)
    issue = JiraRequestHandler.fetchLatestUnsubmittedIssue(session.username, session.version, session.verbose)

    if not issue:
        print(f'No issue found', file=sys.stderr)
        exit(1)

    description: str = issue.toPerforceDescription(withId=True)
    P4Helper.moveFilesInDefaultToNewChangelist(description)