
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

import sys
sys.path.append(PARENT_DIR)

import settings

from requests.auth import HTTPBasicAuth
import requests
from getpass import getpass
from typing import List, Dict

from dateutil.parser import isoparse
from datetime import datetime

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from tabulate import tabulate
import time

import re

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

class BuildJob:
    def __init__(self, data: dict):

        valid = (len(data['events']) > 0)

        try:
            self.deployer = data['events'][0]['user'] if valid else None
        except KeyError:
            self.deployer = None

        self.changelist: int = int(data.get('changelist'))
        self.buildId: str = data.get('buildId')
        self.status: str = data.get('status')
        self.customized: bool = data.get('customized')
        self.operatingSystem: str = data.get('operatingSystem')
        self.deployDate: datetime = data.get('startDate')
        self.version = data.get('version')

        if self.customized is not None:
            self.customized = 'custom' if self.customized else 'standard'

        if self.deployDate:
            self.deployDate = isoparse(self.deployDate)

    def isDone(self) -> bool:
        return self.status.lower() == 'done'

    def isLinux(self) -> bool:
        return 'linux' in self.operatingSystem.lower()

    def isWindows(self) -> bool:
        return 'windows' in self.operatingSystem.lower()

    def isValid(self) -> bool:
        return all([self.deployer])

    def relevancy(self) -> int:

        statusPriority = ('DONE', 'TAKEN', 'FAILED', 'STOPPED', 'PURGED')
        toReturn = len(statusPriority)

        for s in statusPriority:

            if self.status.lower() == s.lower():
                break
            
            toReturn -= 1

        return toReturn

class DeploymentJob:
    def __init__(self, data: dict):

        self.testPackage = data.get('testPackage')
        self.nickname = data.get('nickname')
        self.id = data.get('id')
        self.status = data.get('analysisStatus')
        self.state = data.get('status')
        self.owner = data.get('owner')
        self.buildId: str = data.get('buildId')
        self.feeder = data.get('feederGroup')
        self.pushDate = data.get('pushDate')

        self.changelist = int(self.buildId.split('-')[0]) if self.buildId else None

    def __hash__(self):
        return hash((self.testPackage, self.nickname))

    def __eq__(self, other):
        
        if not isinstance(other, DeploymentJob):
            return False

        return self.testPackage == other.testPackage and self.nickname == other.nickname

    def isFailed(self) -> bool:
        return self.status == 'FAILED' or self.status == 'REQUESTED_FOR_ANALYSIS'

    def isPassed(self) -> bool:
        return self.status == 'PASSED'

    def isKept(self) -> bool:
        return self.state == 'KEPT'

    def makeDateReadable(self):

        date = isoparse(self.pushDate)
        self.pushDate = date.strftime("%b %d %I:%M %p")

    def isValid(self) -> bool:
        return all([self.id, self.pushDate, self.status])

class GqafApiInput:
    def __init__(self):
        self.alreadyPrepared = False # can only prepare an input ONCE

    def isValid(self) -> bool:
        raise NotImplementedError("Abstract method, please override")

    def prepare(self):

        if self.alreadyPrepared:
            return
        
        assert self.isValid(), f'GQAF {self.__class__.__name__} is invalid'

        noneAttributes: List[str] = [attr for attr, value in self.__dict__.items() if value is None]

        for attr in noneAttributes:
            delattr(self, attr)

        self.alreadyPrepared = True

    def toJson(self) -> dict:
        
        if not self.alreadyPrepared:
            self.prepare()

        data = dict(self.__dict__)
        data.pop('alreadyPrepared', None)

        return data

class BuildJobInput(GqafApiInput):

    osMap = {
        "linux" : "Linux-rhel-8.6-x86_64",
        "windows" : "Windows-x86-5.2-64b",
    }

    def __init__(self):

        super().__init__()

        # required
        self.version: str = None
        self.changelist: int = None

        # optional
        self.owner: str = None

        self.customize: str = None
        self.operatingSystems: List[str] = []

        self.shelvedChangelists: List[int] = []

        self.javaProperties: Dict[str, str] = {}
        self.binaryProperties: Dict[str, str] = {}

        self.force: bool = None
        self.mts: bool = None
        self.skipJava: bool = None

        self.priority: int = None

    # override
    def prepare(self):

        if self.alreadyPrepared:
            return

        self.operatingSystems = [BuildJobInput.osMap.get(os, os) for os in self.operatingSystems] # 'linux' -> 'Linux-rhel-8.6-x86_64' etc..
        self.changelist = str(self.changelist)

        if len(self.operatingSystems) == 0:
            self.operatingSystems = None

        if len(self.shelvedChangelists) == 0:
            self.shelvedChangelists = None

        if len(self.javaProperties) == 0:
            self.javaProperties = None

        if len(self.binaryProperties) == 0:
            self.binaryProperties = None

        if not self.force:
            self.force = None

        if not self.mts:
            self.mts = None

        super().prepare() # removes None attributes, among other things

    # override
    def isValid(self) -> bool:

        invalidOs = [os for os in self.operatingSystems if os not in BuildJobInput.osMap.values()]
        if len(invalidOs) >= 1:
            return False

        return all([self.version, self.changelist]) and isinstance(self.changelist, str) # required inputs

class DeploymentJobInput(GqafApiInput):

    def __init__(self):

        super().__init__()

        # required
        self.testPackage: str = None # example: PAR.TPK.0000366
        self.nickname: str = None # example: DEFAULT_1

        self.versionValidationId: str = None # example: PAR.ATOK.0000217

        self.buildId: str = None
        self.waitingBuildId: str = None

        # optional
        self.version: str = None
        self.operatingSystem: str = "Linux-rhel-8.6-x86_64"
        self.changelist: int = None
        self.queue: str = None
        self.keepIfFailed: bool = None
        self.unofficial: bool = None
        self.priority: int = None

    def __str__(self) -> str:
        return f'{self.testPackage} - {self.nickname}'

    def setBuildId(self, newBuildId: str):
        self.buildId = newBuildId

    def getChangelist(self) -> int:

        if self.changelist:
            return self.changelist

        assert self.buildId or self.waitingBuildId, 'no buildId to parse CL from'
        
        if self.waitingBuildId:
            return int(self.waitingBuildId.split('-')[0])

        return int(self.buildId.split('-')[0])

    # override
    def prepare(self):

        if self.alreadyPrepared:
            return

        if self.keepIfFailed == False:
            self.keepIfFailed = None

        if self.unofficial == False:
            self.unofficial = None

        if self.changelist:
            self.changelist = str(self.changelist)

        super().prepare() # removes None attributes, among other things

    # override
    def isValid(self) -> bool:

        if not self.buildId and not self.waitingBuildId:
            return False

        return all([self.testPackage, self.nickname, self.versionValidationId]) # required inputs

class GqafRequestHandler:
    @staticmethod
    def buildDefaultHeaders() -> dict:
        return {'Authorization': f'Bearer {settings.getGqafApiToken()}', 'Accept': 'application/json'}

    @staticmethod
    def authenticate(username: str, password: str) -> str:

        response = requests.get("https://icarus:10113/pc/auth", headers={'Accept':'application/json'}, auth=HTTPBasicAuth(username, password), verify=False)

        if response.status_code == 401:
            return None

        accessToken = response.json().get('jwt', None)
        return accessToken

    @staticmethod
    def authenticateUserThroughSettings(cmdFallback: bool = True) -> str:

        print('Trying to authenticate GQAF using credentials from settings JSON...', file=sys.stderr)

        username: str = settings.getUsername()
        password: str = tryDecrypt(settings.getEncryptedPassword())

        if not username or not password:
            print(f'Failed to authenticate using settings JSON. Please authenticate through CMD', file=sys.stderr)
            return GqafRequestHandler.authenticateUserThroughCmd() if cmdFallback else None

        accessToken: str = GqafRequestHandler.authenticate(username, password)

        if accessToken is None:
            print(f'Failed to authenticate using settings JSON. Please authenticate through CMD', file=sys.stderr)
            return GqafRequestHandler.authenticateUserThroughCmd() if cmdFallback else None

        settings.setSetting('gqaf_token', accessToken)
        return accessToken

    @staticmethod
    def authenticateUserThroughCmd() -> str:

        print('Authenticate into GQAF', file=sys.stderr)

        accessToken: str = None
        while accessToken is None:

            username: str = input('username: ')
            password: str = getpass('password: ')

            accessToken = GqafRequestHandler.authenticate(username, password)

            if accessToken is None:
                print(f'Wrong username or password. Try again.', file=sys.stderr)
                continue # ask again

        settings.setSetting('gqaf_token', accessToken)
        return accessToken

    @staticmethod
    def tryAuthenticate(cmdFallback: bool = True) -> str:

        return GqafRequestHandler.authenticateUserThroughSettings(cmdFallback)

    @staticmethod
    def postRequest(endpoint: str, jsonData: dict) -> requests.Response:

        headers = GqafRequestHandler.buildDefaultHeaders()
        headers['Content-Type'] = 'application/json'
        
        response = None
        try:
            response = requests.post(endpoint, headers=headers, json=jsonData, verify=False)
        except requests.exceptions.ConnectionError:
                print(f'\nCould not reach GQAF endpoint: {endpoint}', file=sys.stderr)
                print('Make sure you are connected to the internet.', file=sys.stderr)
                print('If you are not on Murex premises, make sure you\'re connected through a VPN.', file=sys.stderr)
                exit(2)

        if response.status_code == 401:

            print('GQAF Token expired', file=sys.stderr)
            GqafRequestHandler.tryAuthenticate()
            return GqafRequestHandler.postRequest(endpoint, jsonData)

        if response.status_code >= 400:
            message = response.json().get('errorMessage') or response.json().get('exception')
            if message:
                print(message, file=sys.stderr)
            else:
                print(f'Error occured in POST request:\n{response.text}', file=sys.stderr)

        return response

    @staticmethod
    def getRequest(endpoint: str) -> requests.Response:
        
        response = None
        try:
            response = requests.get(endpoint, headers=GqafRequestHandler.buildDefaultHeaders(), verify=False)
        except requests.exceptions.ConnectionError:
                print(f'\nCould not reach GQAF endpoint: {endpoint}', file=sys.stderr)
                print('Make sure you are connected to the internet.', file=sys.stderr)
                print('If you are not on Murex premises, make sure you\'re connected through a VPN.', file=sys.stderr)
                exit(2)

        if response.status_code == 401:

            print('GQAF Token expired', file=sys.stderr)
            GqafRequestHandler.tryAuthenticate()
            return GqafRequestHandler.getRequest(endpoint)

        if response.status_code != 200:
            message = response.json().get('errorMessage') or response.json().get('exception')
            if message:
                print(message, file=sys.stderr)
            else:
                print(f'Error occured in GET request:\n{response.text}', file=sys.stderr)

        return response

    @staticmethod
    def getAllMxVersions() -> List[str]:

        response: requests.Response = GqafRequestHandler.getRequest('https://icarus:10113/pc/version/all/name')

        if response.status_code != 200:
            return None

        jsonData = response.json()
        return list(jsonData["versions"]["version"])

    @staticmethod
    def fetchVersionDetailsJson(version: str) -> dict:

        print(f'Fetching details of {version}...', file=sys.stderr)
        response: requests.Response = GqafRequestHandler.getRequest('https://icarus:10113/pc/version/' + version)

        if response.status_code != 200:
            return None

        return response.json()

    @staticmethod
    def getVersionValidationAtok(version: str) -> str:
        atok = settings.getVersionIdCache().get(version)
        if atok:
            return atok

        versionDetailsJson = GqafRequestHandler.fetchVersionDetailsJson(version)

        atok = versionDetailsJson["versionValidations"]["versionValidation"][0]["id"]
        settings.cacheVersionAtok(version, atok)
        return atok

    @staticmethod
    def fetchSetupsJson(version: str) -> dict:

        print(f'Fetching setups on {version}...', file=sys.stderr)

        response: requests.Response = GqafRequestHandler.getRequest('https://icarus:10113/pc/setup/jobs' + '?versions=' + version)

        if response.status_code != 200:
            return None

        return response.json()

    @staticmethod
    def removeDuplicates(buildJobs: List[BuildJob]):

        # for some reason, a job will sometimes appear as 2 jobs with buildIds that differ by 1
        # the one with the higher buildId is usually the correct one

        def buildIdToInt(jobBuildId: str) -> int:
            s = ''.join(c for c in jobBuildId if c.isdigit())
            return int(s)

        toRemove: List[int] = []

        for i, job in enumerate(buildJobs):

            if i == len(buildJobs)-1:
                break

            if job.buildId is None:
                continue

            currentOs = job.operatingSystem
            nextOs = buildJobs[i+1].operatingSystem

            if currentOs != nextOs:
                continue

            currentBuildId = buildIdToInt(job.buildId)
            nextBuildId = buildIdToInt(buildJobs[i+1].buildId)

            if currentBuildId - 1 == nextBuildId:
                toRemove.append(i+1) # remove the buildId with the lower value

            continue

        for index in reversed(toRemove):
            buildJobs.pop(index)

        return

    @staticmethod
    def fetchBuildJobs(version: str, changelistFilter: int = None, ownerFilter: str = None) -> List[BuildJob]:

        json = GqafRequestHandler.fetchSetupsJson(version)

        if json is None:
            return None

        buildJobs = json["productionJobs"]["productionJob"]
        buildJobs = [BuildJob(job) for job in buildJobs]
        buildJobs = [job for job in buildJobs if job.isValid()]
        GqafRequestHandler.removeDuplicates(buildJobs)

        if changelistFilter:
            buildJobs = [job for job in buildJobs if job.changelist == changelistFilter]

        if ownerFilter:
            buildJobs = [job for job in buildJobs if job.deployer == ownerFilter]

        return buildJobs

    @staticmethod
    def fetchDeploymentJobsJson(version: str) -> dict:

        print(f'Fetching jobs on {version}...', file=sys.stderr)
        versionAtok = GqafRequestHandler.getVersionValidationAtok(version)
        response: requests.Response = GqafRequestHandler.getRequest('https://icarus:10113/pc/deployment' + f'?versionvalidationid={versionAtok}')

        if response.status_code != 200:
            return None

        return response.json()

    @staticmethod
    def fetchDeploymentJobs(version: str, changelistFilter: int = None, ownerFiler: str = None) -> List[DeploymentJob]:

        json = GqafRequestHandler.fetchDeploymentJobsJson(version)

        if json is None:
            return None

        deploymentJobs = json["deploymentJobDetails"]["deploymentJobDetail"]
        deploymentJobs = [DeploymentJob(job) for job in deploymentJobs]
        deploymentJobs = [job for job in deploymentJobs if job.isValid()]
        deploymentJobs.sort(key=lambda job: isoparse(job.pushDate), reverse=True) # sort by most recent

        if changelistFilter:
            deploymentJobs = [job for job in deploymentJobs if job.buildId.startswith(str(changelistFilter))]

        if ownerFiler:
            deploymentJobs = [job for job in deploymentJobs if job.owner == ownerFiler]

        [job.makeDateReadable() for job in deploymentJobs]

        return deploymentJobs

    @staticmethod
    def pushBuildJob(input: BuildJobInput) -> int: # returns commandId of the pushed job

        print(f'Pushing build job on {input.version}, CL: {input.changelist}...', file=sys.stderr)
        response: requests.Response = GqafRequestHandler.postRequest("https://icarus:10113/pc/version/build", jsonData=input.toJson())

        if response.status_code != 201:
            return None

        return response.json().get('jobId', None)

    @staticmethod
    def pushDeploymentJob(input: DeploymentJobInput) -> str: # returns PAR_DJOB_ID

        print(f'\nPushing: {input} on {input.version}, CL: {input.getChangelist()}', file=sys.stderr)
        response: requests.Response = GqafRequestHandler.postRequest("https://icarus:10113/pc/deployment", jsonData=input.toJson())

        if response.status_code != 201:
            return None

        parDjobId: str =response.json().get('jobId', None)
        return parDjobId

def printObjectList(objects: List[object], csv: bool = False):

    if len(objects) == 0:
        return

    print(end='\n', file=sys.stderr)

    tableContent = [obj.__dict__.values() for obj in objects]
    headers = [key.capitalize() for key in objects[0].__dict__.keys()]

    if csv:
        fullTable: str = tabulate(tableContent, headers=headers, tablefmt='tsv').replace('\t', ',')
        fullTable = re.sub(r'\s*,\s*', r',', fullTable)
    else:
        fullTable: str = tabulate(tableContent, headers=headers)

    headerCutOff = 1 if csv else 2
    headerContent = '\n'.join(fullTable.split('\n')[:headerCutOff])
    tableContent = '\n'.join(fullTable.split('\n')[headerCutOff:])

    if not len(tableContent):
        return

    print(headerContent, file=sys.stdout if csv else sys.stderr, end='\n\n')
    time.sleep(0.005) # this is to avoid stderr getting mixed with stdout, force headers to first line

    try:
        print(tableContent)
    except BrokenPipeError: # some commands like "head" will close the pipe early and prevent the program from outputting more lines
        pass