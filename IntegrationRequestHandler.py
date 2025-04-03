
import argparse
import os

import settings
from SessionInfo import SessionInfo
from p4Helper import P4Helper, Changelist
from gqaf.GqafRequestHandler import GqafRequestHandler

import re
import json

import requests
from typing import List, Dict, Set

import sys

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from gqaf.GqafRequestHandler import ApiJsonInput

class IntegrationInput(ApiJsonInput):

    def __init__(self):

        super().__init__()

        self.defectIds: List[str] = []

        self.destinationVersion: str = P4Helper.Build
        self.sourceVersion: str = None

        self.requester: str = None
        self.notificationList: List[str] = [] # list of usernames, not emails

        self.interactiveDefectIds: List[str] = []

        self.integrateWithForce: bool = False
        self.integrateWithDelete: bool = False

        self.fullQualityGateBuild: bool = True

    def __str__(self) -> str:

        s = str()

        s += ', '.join(self.defectIds)
        s += f'\nFrom {self.sourceVersion} to {self.destinationVersion}'
        s += f'\nNotification list: {",".join(self.notificationList)}'
        s += f'\n-f: {self.integrateWithForce}'
        s += f'\n-d: {self.integrateWithDelete}'
        s += f'\nQuality gate build: {self.fullQualityGateBuild}'

        return s

    # override
    def isValid(self) -> bool:
        
        if not self.defectIds:
            print(f'No defects to integrate', file=sys.stderr)
            return False

        for defect in self.defectIds:

            if re.match(P4Helper.DefectRegex, defect):
                continue

            print(f'Not a defect: {defect}', file=sys.stderr)
            return False

        if not all([self.destinationVersion, self.sourceVersion, self.requester, self.notificationList]):
            print(f'Missing required fields in Integration Bot input', file=sys.stderr)
            return False

        return True

    def prepare(self):

        self.defectIds = [d for d in self.defectIds if d] # remove null defects
        self.defectIds = list(set(self.defectIds))

        self.interactiveDefectIds = [d for d in self.interactiveDefectIds if d] # remove null defects
        self.interactiveDefectIds = list(set(self.interactiveDefectIds))

        super().prepare()

    def addDefect(self, d: str):

        d = d.upper().strip()
        assert re.match(P4Helper.DefectRegex, d), f'{d} is not a defect'

        self.defectIds.append(d)

class IntegrationRequestHandler:

    @staticmethod
    def integrateToMainstream(input: IntegrationInput) -> str:
        
        from JenkingsRequestHandler import JenkinsRequestHandler
        print(f'Integrating {len(input.defectIds)} defect(s) to mainsream...', file=sys.stderr)
        success: bool = JenkinsRequestHandler.lynxPipelineIntegrateToMainstream(input)

        if not success:
            return False

        return True

    @staticmethod
    def buildHeaders() -> dict:
        return {'Accept': 'application/json'}

    @staticmethod
    def buildAuth() -> tuple:
        raise NotImplementedError()

    @staticmethod
    def buildParams() -> dict:
        raise NotImplementedError()

    @staticmethod
    def postRequest(endpoint: str) -> requests.Response:
        raise NotImplementedError()

def readFileLines(filePath: str) -> List[str]:

    assert os.path.isfile(filePath), f'Not a file: {filePath}'

    with open(filePath, 'r') as file:
        return file.readlines()

def readStdinLines() -> List[str]:

    print(f"reading from stdin...", file=sys.stderr)
    return sys.stdin.read().splitlines()

def parseChangelistFromLine(line: str, verbose: bool = False) -> Changelist:

    pattern: str = r'\b(\d+)\b'
    m = re.search(pattern, line)
    if not m:
        return None

    cl = P4Helper._getChangelist(m.group(1))
    return cl

def parseIntegrationInputFromLines(changelistLines: List[str], verbose: bool = False) -> IntegrationInput:

    clsToIntegrate: List[Changelist] = []
    versionSet: Set[str] = set()
    devSet: Set[str] = set()

    for line in changelistLines:

        cl = parseChangelistFromLine(line, verbose=verbose)
        if not cl:
            if verbose:
                print(f'No changelist found on line: {line}', file=sys.stderr)
            continue

        if not cl.defect:
            print(f'[WARN] Changelist has no defect: {cl}', file=sys.stderr)
            continue

        print(f'Parsed: {cl}', file=sys.stderr)

        clsToIntegrate.append(cl)
        versionSet.add(cl.version)
        devSet.add(cl.developer)

    print(end='\n', file=sys.stderr)

    if len(clsToIntegrate) == 0:
        print(f'No changelists were parsed. Nothing to integrate.', file=sys.stderr)
        exit(0)

    if len(versionSet) > 1:
        print(f'[ERROR] Trying to integrate from multiple versions: {", ".join(v for v in versionSet)}', file=sys.stderr)
        exit(1)

    if len(devSet) > 1:
        print(f'[WARN] You are integrating multiple developers defects: {", ".join(dev for dev in devSet)}', file=sys.stderr)

    input = IntegrationInput()
    input.sourceVersion = next(iter(clsToIntegrate)).version

    for cl in clsToIntegrate:
        input.addDefect(cl.defect)

    return input

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Integrate to mainstream from changelist input')

    parser.add_argument('file_to_parse', nargs='?', default=None, help='File to parse changelists from, otherwise parse from stdin')

    parser.add_argument('-f', '--force', action='store_true', default=False, help='Integrate with -f force', required=False)
    parser.add_argument('-d', '--delete', action='store_true', default=False, help='Integrate with -d delete', required=False)
    parser.add_argument('--send', action='store_true', default=False, help='Immediately send an api request which integrates into build', required=False)

    args, _ = parser.parse_known_args()

    session = SessionInfo()

    if session.version is None:
        print(f'Cannot integrate without source -v version', file=sys.stderr)
        session.close()
        exit(1)

    linesToParse: List[str] = []
    if not args.file_to_parse:
        linesToParse = readStdinLines()
    else:
        fileToParse: str = args.file_to_parse.strip()
        if not os.path.exists(fileToParse):
            print(f'Path does not exist: {fileToParse}')
            exit(1)

        if not os.path.isfile(fileToParse):
            print(f'Not a file: {fileToParse}')
            exit(1)

        linesToParse = readFileLines(fileToParse)

    inputs: IntegrationInput = parseIntegrationInputFromLines(linesToParse, verbose=session.verbose)
    inputs.requester = session.username

    inputs.integrateWithForce = args.force
    inputs.integrateWithDelete = args.delete
    inputs.fullQualityGateBuild = True

    if inputs.sourceVersion != session.version:
        print(f'Parsed changelists\' version different from specified version.', file=sys.stderr)
        print(f'Version parsed from changelists: {inputs.sourceVersion}', file=sys.stderr)
        print(f'Version specified using -v: {session.version}', file=sys.stderr)
        session.close()
        exit(1)

    versionOwners: List[str] = GqafRequestHandler.fetchVersionOwners(inputs.sourceVersion)

    inputs.notificationList = settings.getSetting('notification_list')
    inputs.notificationList.extend(versionOwners)

    versionSubmitters: List[str] = list(cl.developer for cl in P4Helper.getChangelists(inputs.sourceVersion, verbose=session.verbose))
    print(f'Getting changelists on {P4Helper.Build}...', file=sys.stderr)
    defectsInMainstream: Dict[str, Changelist] = P4Helper.extractMergedDefects(inputs.defectIds, P4Helper.Build, set(versionOwners + versionSubmitters))

    print(end='\n', file=sys.stderr)
    for defect, cl in defectsInMainstream.items():
        print(f'[WARN] {cl.defect} already on v3.1.build: {cl}', file=sys.stderr)

    if len(defectsInMainstream) > 0 and not inputs.integrateWithForce:
        print(f'[ERROR] Since the defects above are already on v3.1.build, the only way to integrate is with -f force', file=sys.stderr)
        session.close()
        exit(1)

    print(end='\n', file=sys.stderr, flush=True)
    print('READY TO INTEGRATE', end='\n\n', file=sys.stderr, flush=True)

    inputJson: str = json.dumps(inputs.toJson())
    print(inputJson, file=sys.stdout, flush=True)

    if args.send:

        success = bool(IntegrationRequestHandler.integrateToMainstream(inputs))
        if not success:
            exit(1)

    session.close()
    exit(0)