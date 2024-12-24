
import argparse
import sys
import json

from typing import List, Dict
from GqafRequestHandler import GqafRequestHandler, printObjectList, BuildJob
from SessionInfo import SessionInfo
from p4Helper import Changelist

class SetupsViewRow:

    def __init__(self, changelist: Changelist, setupsPool: Dict[int, List[BuildJob]]):
        
        self.developer = changelist.developer
        self.changelist = changelist.value
        # self.description = changelist.description

        self.windows = '-----'
        self.linux = '-----'
        
        self.linuxBuildId = None
        self.deployDate = None

        for build in setupsPool.get(self.changelist, dict()):

            self.deployDate = build.deployDate

            if build.isLinux():
                self.linux = build.status
                self.linuxBuildId = build.buildId

            elif build.isWindows():
                self.windows = build.status

            continue

        return

def printBreakdownByChangelist(setupsPool: Dict[int, List[BuildJob]], changelistPool: List[Changelist]):

    setupsList: List[SetupsViewRow] = []

    for cl in changelistPool:

        row = SetupsViewRow(cl, setupsPool)
        setupsList.append(row)

    printObjectList(setupsList)

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Fetch setups')
    parser.add_argument('--json', action='store_true', default=False, help='Output in JSON format')
    parser.add_argument('--breakdown', action='store_true', default=False, help='Breakdown the view by changelist')

    args, _ = parser.parse_known_args()

    session = SessionInfo()

    if not session.version:
        print('Cannot get setups without specifying version', file=sys.stderr)
        exit(1)

    if args.breakdown:

        session.fetchChangelistPool(lazy=True, limit=30)
        session.fetchSetupsPool(lazy=True)

        printBreakdownByChangelist(session.setupsPool, session.changelistPool)
        exit(0)
        
    if args.json:
        buildJobs: dict = GqafRequestHandler.fetchDeploymentJobsJson(session.version)

        if buildJobs is None:
            print('Failed to fetch setups', file=sys.stderr)
            exit(1)

        print(json.dumps(buildJobs, indent=4), file=sys.stdout)
        exit(0)

    ownerFilter = session.username if session.usernameSpecifiedThroughCmd else None
    buildJobs: List[BuildJob] = GqafRequestHandler.fetchBuildJobs(session.version, session.changelist, ownerFilter)

    if buildJobs is None:
        print('Failed to fetch setups', file=sys.stderr)
        exit(1)

    printObjectList(buildJobs)
    exit(0)