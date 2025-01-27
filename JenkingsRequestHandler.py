
import settings

import json
import re

import requests
from getpass import getpass
from typing import List, Dict

import sys

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

class JenkinsBuild:

    def __init__(self, data: dict):

        self.number = data.get('number')
        self.url = data.get('url')

        self.displayName = data.get('displayName')
        m = re.search(r'CL\s*(\d+)', self.displayName)
        if m:
            self.changelist: int = int(m.group(1))
        else:
            self.changelist = None

        self.building: bool = data.get('building')
        self.result: str = data.get('result')

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
        password = tryDecrypt(settings.getEncryptedPassword())
        
        if not password:
            password: str = getpass(f'{username} password for jenkins API: ')

        return (username, password)

    @staticmethod
    def buildParams() -> dict:

        return {'tree': 'displayName,description,builds[number,status,displayName,url,result,building]'}

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
        print(f'Fetching a pipeline on {version}...', end='\n\n', file=sys.stderr)

        pipelineLink = pipelineLink.strip('/') + '/api/json'
        response = JenkinsRequestHandler.getRequest(pipelineLink)

        if not response:
            return None

        data = response.json()
        return PipelineInfo(data)

def getPipelineBuildsByChangelist(pipeline: PipelineInfo) -> Dict[int, JenkinsBuild]:

    builds: Dict[int, JenkinsBuild] = {}
    for build in reversed(pipeline.builds):
        if build.changelist:
            builds[build.changelist] = build

    return builds

if __name__ == '__main__':

    # example usage
    version = settings.getCurrentVersion()
    alienCppValidation = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{version}/job/CppValidation/'
    pipeline: PipelineInfo = JenkinsRequestHandler.getPipelineInfo(alienCppValidation)

    if not pipeline:
        print(f'Couldn\'t get pipeline info')
        exit(1)

    print(pipeline.name)
    builds = getPipelineBuildsByChangelist(pipeline)
    for cl in sorted(builds.keys(), reverse=True):

        build = builds.get(cl)
        print(build)