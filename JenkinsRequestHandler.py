
import settings
from SessionInfo import SessionInfo

import re

import requests
from typing import List, Dict

import sys
import os
import time

CURRENT_DIR = sys.path[0]
sys.path.append(os.path.join(CURRENT_DIR, 'gqaf'))

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from enum import Enum, auto

class FailureReason(Enum):

    Unknown = auto()
    CompileFailed = auto()
    BuildFailed = auto()
    FailedTests = auto()
    MemoryLeak = auto()
    UseAfterFree = auto()
    TestCrash = auto()
    SegFault = auto()
    BufferOverflow = auto()
    AllocDeallocMismatch = auto()

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

        self.startTimestamp = data.get('timestamp')

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

        if 'unstable' in self.result.lower():
            return 'UNSTABLE'

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

    def getRunningTimeMinutes(self) -> int:

        if not self.startTimestamp:
            return None

        if self.isDone():
            return None

        now = int(time.time() * 1000)
        delta = now - self.startTimestamp
        return int(delta / 60000)

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

            # Build Failed
            m = re.search(r'BUILD\s+FAILURE', line)
            if m:
                return (FailureReason.BuildFailed, 'Build Failure')

            # Failed GTest(s)
            m = re.search(r'\[\s*FAILED\s*\]\s*(\d+)\s*test.*listed\s*below', line)
            if m:
                numberOfFailedTests = int(m.group(1))
                failedTests: str = ' | '.join([re.search(r'\[\s*FAILED\s*\]\s*(\S+)', l).group(1) for l in logLines[i+1: i+numberOfFailedTests+1]])
                return (FailureReason.FailedTests, f'({numberOfFailedTests}) ' + failedTests)

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
                m = re.search(r'RUN\s*\]\s*(\S+)', logLines[i-1])
                back = 2
                while not m:
                    m = re.search(r'RUN\s*\]\s*(\S+)', logLines[i-back])
                    back += 1

                testThatCrashed: str = m.group(1)
                return (FailureReason.TestCrash, testThatCrashed)

            # Segmentation Fault
            m = re.search(r'addresssanitizer:deadlysignal', line, re.IGNORECASE)
            if m:
                guilyTest: str = re.search(r'RUN\s*\]\s*(\S+)', logLines[i-1]).group(1)
                return (FailureReason.SegFault, guilyTest)

            # Stack Buffer Overflow
            m = re.search(r'ERROR:\s+AddressSanitizer:\s+stack-buffer-overflow', line, re.IGNORECASE)
            if m:
                return (FailureReason.BufferOverflow, 'BufferOverflow')

            # Alloc Dealloc Mismatch
            m = re.search(r'ERROR:\s+AddressSanitizer:\s+alloc-dealloc-mismatch', line, re.IGNORECASE)
            if m:
                return (FailureReason.AllocDeallocMismatch, 'AllocDeallocMismatch')

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
    def buildDefaultHeaders() -> dict:
        return {'Accept': 'application/json'}

    @staticmethod
    def buildAuth() -> tuple:

        username = settings.getUsername()
        token = settings.getJenkinsApiToken()

        if not token:
            print(f'Jenkinds API token not found. Please set it in your settings JSON file as "jenkins_token"', file=sys.stderr)

        return (username, token)

    @staticmethod
    def buildPipelineInfoParams() -> dict:
        return {'tree': 'displayName,description,builds[number,status,timestamp,displayName,description,url,result,building,artifacts[relativePath]]'}

    @staticmethod
    def postRequest(endpoint: str, jsonData: dict = None, params: dict = None, headers: dict = None) -> requests.Response:

        if headers is None:
            headers = JenkinsRequestHandler.buildDefaultHeaders()

        headers['Content-Type'] = 'application/json'
        
        response = None
        try:
            response = requests.post(endpoint, headers=headers,
                                    json=jsonData,
                                    params=params,
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

            print(f'Not found: {endpoint}', file=sys.stderr)
            return None

        if response.status_code not in [200, 201]:

            print(f'Error occured in POST request:\n{response.text}', file=sys.stderr)
            return None

        return response

    @staticmethod
    def getRequest(endpoint: str, params: dict = None) -> requests.Response:
        
        response = None
        try:
            response = requests.get(endpoint, headers=JenkinsRequestHandler.buildDefaultHeaders(),
                                    params=params,
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

            print(f'Not found: {endpoint}', file=sys.stderr)
            return None

        if response.status_code != 200:

            print(f'Error occured in GET request:\n{response.text}', file=sys.stderr)
            return None

        return response

    from IntegrationRequestHandler import IntegrationInput
    @staticmethod
    def lynxPipelineIntegrateToMainstream(input: IntegrationInput) -> bool:

        print(f'Integrating {len(input.defectIds)} defect(s) to mainsream (using Lynx pipeline)...', file=sys.stderr)

        input: dict = input.toJson()

        input['defectIds'] = ','.join(input['defectIds'])
        input['interactiveDefectIds'] = ','.join(input['interactiveDefectIds'])
        input['notificationList'] = ','.join(input['notificationList'])

        for key, value in input.items():
            input[key] = str(value)

        input = {key[0].upper() + key[1:]: value for key, value in input.items()}

        pipelineUrl: str = 'https://cje-core.fr.murex.com/teams-sbp/job/lynx/job/IntegrateToMainstream/buildWithParameters?delay=0sec'

        for key, value in input.items():
            pipelineUrl += f'&{key}={value}'

        crumb: str = JenkinsRequestHandler.getTeamsSbpAuthCrumb()
        if not crumb:
            print(f'Failed to get jenkins auth crumb for user: {settings.getUsername()}...', file=sys.stderr)
            return False

        headersWithCrumb: dict = JenkinsRequestHandler.buildDefaultHeaders()
        headersWithCrumb['Jenkins-Crumb'] = crumb

        response = JenkinsRequestHandler.postRequest(pipelineUrl, headers=headersWithCrumb)

        if not response:
            print(f'Couldn\'t push Lynx CI job', file=sys.stderr)
            return False

        if response.status_code != 201:
            print(f'Couldn\'t push Lynx CI job', file=sys.stderr)
            return False

        print(f'Lynx CI job successfully pushed.', file=sys.stderr)
        pipelineUrl: str = 'https://cje-core.fr.murex.com/teams-sbp/job/lynx/job/IntegrateToMainstream/'
        print(f'URL: {pipelineUrl}', file=sys.stderr)
        print(f'If successful, you will receive an email with the job link.', file=sys.stderr)
        return True

    @staticmethod
    def getTeamsSbpAuthCrumb() -> str:

        print(f'Getting jenkins auth crumb for user: {settings.getUsername()}...', file=sys.stderr)

        endpoint: str = 'https://cje-core.fr.murex.com/teams-sbp/crumbIssuer/api/json'
        response = JenkinsRequestHandler.getRequest(endpoint, params=None)

        if not response:
            return None

        data: dict = response.json()
        crumb: str = data.get('crumb')
        return crumb

    @staticmethod
    def getPipelineInfo(pipelineLink: str) -> PipelineInfo:

        version = re.search(r'/(v3.1.build.*?)\/?$', pipelineLink)
        if version:
            print(f'Fetching a pipeline on {version.group(1)}...', file=sys.stderr)

        pipelineLink = pipelineLink.strip('/') + '/api/json'
        params: dict = JenkinsRequestHandler.buildPipelineInfoParams()
        response = JenkinsRequestHandler.getRequest(pipelineLink, params)

        if not response:
            return None

        jsonData: str = response.text

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

if 0:

    alienFreyja = f'https://cje-core.fr.murex.com/assets/job/FreyjaAlien/job/{SessionInfo().version}/'
    freyjaPipeline: PipelineInfo = JenkinsRequestHandler.getPipelineInfo(alienFreyja)
    freyjaPool = getPipelineBuildsByChangelist(freyjaPipeline)

    exit(0)

if __name__ == '__main__':

    # example usage

    session = SessionInfo()
    version = session.version

    alienAsan = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{version}/job/AsanValidation/'
    asanPipeline: PipelineInfo = JenkinsRequestHandler.getPipelineInfo(alienAsan)
    asanPool = getPipelineBuildsByChangelist(asanPipeline)

    alienCpp = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{version}/job/CppValidation/'
    cppPipeline: PipelineInfo = JenkinsRequestHandler.getPipelineInfo(alienCpp)
    cppPool = getPipelineBuildsByChangelist(cppPipeline)

    from gqaf.RichVersionView import createRichJenkinsView
    createRichJenkinsView(cppPool, asanPool).buildAndPrint(session.fetchChangelistPool(lazy=True, limit=20))