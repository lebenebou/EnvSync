
import settings
import SessionInfo

import re

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

from getpass import getpass

class FailureReason(Enum):

    Unknown = 0
    CompileFailed = 1
    FailedTest = 2
    MemoryLeak = 3
    UseAfterFree = 4
    TestCrash = 5

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

class JenkinsBuild:

    def __init__(self, data: dict):

        self.number = data.get('number')
        self.url: str = data.get('url')

        self.displayName = data.get('displayName')
        self.description = data.get('description')

        self.changelist = None
        # Parse CL from display name
        m = re.search(r'CL\s*(\d+)', self.displayName)
        if m:
            self.changelist: int = int(m.group(1))

        # Parse CL from description
        if self.description:
            m = re.search(r'CL\s*(\d+)', self.description)
        if m and not self.changelist:
            self.changelist: int = int(m.group(1))

        self.building: bool = data.get('building')
        self.result: str = data.get('result')

        self.artifactUrls: List[str] = []
        for artifact in data.get('artifacts', []):

            relativeUrl: str = artifact.get('relativePath')
            fullUrl: str = self.url.strip('/')
            fullUrl += '/artifact/'
            fullUrl += relativeUrl

            self.artifactUrls.append(fullUrl)
            continue

        self.artifactUrls.sort(key=lambda name: 'test' not in name.split('/')[-1].lower())
        self.logs: Dict[str, str] = {}

    def __str__(self) -> str:

        s = str()

        s += f'Build N {self.number}'

        if self.changelist:
            s += f' on CL {self.changelist}'

        s += f': {self.status()}'
        return s

    def status(self) -> str:

        if self.building:
            return 'TAKEN'

        if self.result is None:
            return '----'

        if self.isFailed():
            return 'RED'

        return 'GREEN'

    def isDone(self) -> bool:

        if self.result is None:
            return False

        if self.building:
            return False

        return True

    def isSuccessful(self) -> bool:
        
        if not self.isDone():
            return False

        return self.result == 'SUCCESS'

    def isFailed(self) -> bool:
        
        if not self.isDone():
            return False

        return self.result == 'FAILURE'

    def getLogs(self, artifactName: str) -> str:

        if artifactName in self.logs:
            return self.logs.get(artifactName)

        for url in self.artifactUrls:

            m = re.search(artifactName, url)
            if not m:
                continue

            artifactName: str = m.group()

            response = JenkinsRequestHandler.getRequest(url)
            if response.status_code != 200:
                continue

            self.logs[artifactName] = response.text
            return self.logs.get(artifactName)

        return None

    @staticmethod
    def guessFailureReasonFromLogs(logLines: List[str]) -> tuple[FailureReason, str]:

        if isinstance(logLines, str):
            logLines = logLines.splitlines()

        # returns the possible failure reason with an error message as hint
        for i, line in enumerate(logLines):

            # Compile Error
            m = re.search(r'^\[ERROR\](.*?)error:(.*)$', line)
            if m:
                guiltyFile: re.Match = re.search(r'([^/]*\.(c|cpp))', m.group(1))
                errorMessage: str = m.group(2) if not guiltyFile else guiltyFile.group(1)
                return (FailureReason.CompileFailed, errorMessage)

            # Failed GTest(s)
            m = re.search(r'\[\s*FAILED\s*\]\s*(\d+)\s*test.*listed\s*below', line)
            if m:
                numberOfFailedTests = int(m.group(1))
                failedTests: str = ' | '.join([re.search(r'\[\s*FAILED\s*\]\s*(\S+)', l).group(1) for l in logLines[i+1: i+numberOfFailedTests+1]])
                return (FailureReason.FailedTest, failedTests)

            # Memory Leaks
            m = re.search(r'detected memory leaks', line, re.IGNORECASE)
            if m:
                return (FailureReason.MemoryLeak, 'Memory Leaks')

            # Use After Free
            m = re.search(r'use.after.free', line, re.IGNORECASE)
            if m:
                return (FailureReason.UseAfterFree, 'Use After Free')

            # Test Crash
            m = re.search(r'test crash detected', line, re.IGNORECASE)
            if m:
                testThatCrashed: str = re.search(r'RUN\s*\]\s*(\S+)', logLines[i-1]).group(1)
                return (FailureReason.TestCrash, testThatCrashed)

        return (FailureReason.Unknown, 'Unknown Failure')

    def guessFailureReason(self) -> tuple[FailureReason, str]:

        for artifactUrl in self.artifactUrls:

            artifactBaseName: str = artifactUrl.split('/')[-1]
            logs: str = self.getLogs(artifactBaseName)
            if logs is None:
                continue

            reason, errorMessage = JenkinsBuild.guessFailureReasonFromLogs(logs)
            if reason != FailureReason.Unknown:
                return (reason, errorMessage)

        return (FailureReason.Unknown, 'Unkown Failure')

class PipelineInfo:

    def __init__(self, data: dict):
        
        self.name = data.get('displayName')
        self.description = data.get('description')

        self.builds: List[JenkinsBuild] = []

        for build in data.get('builds', []):

            b = JenkinsBuild(build)
            self.builds.append(b)

class JenkinsRequestHandler:

    @staticmethod
    def buildHeaders() -> dict:
        return {'Accept': 'application/json'}

    @staticmethod
    def buildAuth() -> tuple:

        username = settings.getUsername()
        token = settings.getJenkinsApiToken()

        if not token:
            print(f'Jenkinds API token not found. Please set it in your settings JSON file as "jenkins_token"', file=sys.stderr)

        return (username, token)

    @staticmethod
    def buildParams() -> dict:

        return {'tree': 'displayName,description,builds[number,status,displayName,description,url,result,building,artifacts[relativePath]]'}

    @staticmethod
    def getRequest(endpoint: str) -> requests.Response:
        
        response = None
        try:
            response = requests.get(endpoint, headers=JenkinsRequestHandler.buildHeaders(),
                                    params=JenkinsRequestHandler.buildParams(),
                                    auth=JenkinsRequestHandler.buildAuth(),
                                    verify=False)

        except requests.exceptions.ConnectionError:
                print(f'\nCould not reach Jenkins endpoint: {endpoint}', file=sys.stderr)
                print('Make sure you are connected to the internet.', file=sys.stderr)
                print('If you are not on Murex premises, make sure you\'re connected through a VPN.', file=sys.stderr)
                exit(2)

        if response.status_code == 401:

            print('Wrong username or password. Authentication failed', file=sys.stderr)
            return None

        if response.status_code == 404:

            print(f'Pipeline doesn\'t exist: {endpoint}', file=sys.stderr)
            return None

        if response.status_code != 200:

            print(f'Error occured in GET request:\n{response.text}', file=sys.stderr)
            return None

        return response

    @staticmethod
    def getPipelineInfo(pipelineLink: str) -> PipelineInfo:

        version = re.search(r'/(v3.1.build.*?)/', pipelineLink).group(1)
        print(f'Fetching a pipeline on {version}...', file=sys.stderr)

        pipelineLink = pipelineLink.strip('/') + '/api/json'
        response = JenkinsRequestHandler.getRequest(pipelineLink)

        if not response:
            return None

        data = response.json()
        return PipelineInfo(data)

def getPipelineBuildsByChangelist(pipeline: PipelineInfo) -> Dict[int, JenkinsBuild]:

    if pipeline is None:
        return None

    builds: Dict[int, JenkinsBuild] = {}
    for build in reversed(pipeline.builds):
        if build.changelist:
            builds[build.changelist] = build

    return builds

if __name__ == '__main__':

    # example usage

    version = SessionInfo.SessionInfo().version
    alienAsan = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{version}/job/AsanValidation/'
    alienCpp = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{version}/job/CppValidation/'

    asanPipeline: PipelineInfo = JenkinsRequestHandler.getPipelineInfo(alienAsan)
    cppPipeline: PipelineInfo = JenkinsRequestHandler.getPipelineInfo(alienCpp)

    if not asanPipeline:
        print(f'Couldn\'t get pipeline info')
        exit(1)

    print(cppPipeline.name)
    builds = getPipelineBuildsByChangelist(cppPipeline)
    for cl in sorted(builds.keys(), reverse=True):

        build = builds.get(cl)
        print(build, end='\t')
        if build.isFailed():
            print(build.guessFailureReason(), end='')

        print(flush=True)

    print()
    print(asanPipeline.name)
    builds = getPipelineBuildsByChangelist(asanPipeline)
    for cl in sorted(builds.keys(), reverse=True):

        build = builds.get(cl)
        print(build, end='\t')
        if build.isFailed():
            print(build.guessFailureReason(), end='')

        print(flush=True)