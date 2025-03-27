
import settings

from SessionInfo import SessionInfo
from p4Helper import P4Helper
from gqaf.GqafRequestHandler import GqafRequestHandler

import re

import requests
from typing import List, Dict

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
        self.interactiveDefectIds = [d for d in self.interactiveDefectIds if d] # remove null defects

        super().prepare()

    def addDefect(self, d: str):

        d = d.upper().strip()
        assert re.match(P4Helper.DefectRegex, d), f'{d} is not a defect'

        self.defectIds.append(d)

class IntegrationRequestHandler:

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

if __name__ == '__main__':
    
    session = SessionInfo()
    version: str = session.version

    recentDefects: List[str] = [cl.defect for cl in P4Helper.getChangelists(version, limit=15)]
    mainstreamDefects = P4Helper.extractMainstreamDefects(recentDefects, GqafRequestHandler.fetchVersionOwners(version))

    for defect, cl in mainstreamDefects.items():
        print(f'[WARN] {defect} was submitted on {cl}')

    session.close()