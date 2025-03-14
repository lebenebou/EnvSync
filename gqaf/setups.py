
import argparse
import sys
import json
import re

from typing import List, Dict
from GqafRequestHandler import GqafRequestHandler, printObjectList, BuildJob
from SessionInfo import SessionInfo
from p4Helper import Changelist

class SetupsViewRow:

    def __init__(self, changelist: Changelist, setupsPool: Dict[int, List[BuildJob]]):
        
        # self.deployer = None
        self.developer = changelist.developer
        self.changelist = changelist.value

        self.windows = '-----'
        self.linux = '-----'
        self.buildId = '-----'

        bestLinuxBuild: BuildJob = None
        bestWindowsBuild: BuildJob = None

        for build in setupsPool.get(changelist.value, []):

            if build.isLinux():
                bestLinuxBuild = SetupsViewRow.moreRelevantBuild(bestLinuxBuild, build)

            elif build.isWindows():
                bestWindowsBuild = SetupsViewRow.moreRelevantBuild(bestWindowsBuild, build)

        if bestLinuxBuild:
            self.linux = bestLinuxBuild.status
            self.buildId = bestLinuxBuild.buildId
            # self.deployer = bestLinuxBuild.deployer

        if bestWindowsBuild:
            self.windows = bestWindowsBuild.status

        self.description = f'[{changelist.defect}]{changelist.allTags()}{changelist.description[:30]}'
        return

    @staticmethod
    def moreRelevantBuild(b1: BuildJob, b2: BuildJob):

        if b1 is None or b2 is None:
            return b1 if b1 else b2

        if b1.isCustomized() != b2.isCustomized():
            return b1 if b2.isCustomized() else b2

        if b1.status == b2.status:
            return b1 if b1.deployDate > b2.deployDate else b2 # more recent build

        statusPriority = ('DONE', 'TAKEN', 'FAILED', 'STOPPED', 'PURGED')
        for status in statusPriority:

            if status in (b1.status, b2.status):
                return b1 if b1.status == status else b2

        return b2

def setupsRowsFromSession(session: SessionInfo, limit: int = 20) -> List[SetupsViewRow]:

    session.fetchChangelistPool(lazy=True, limit=limit)
    session.fetchSetupsPool(lazy=True)

    rows: List[SetupsViewRow] = [] # for each changelist in ascending order, get the most relevant build job and add it as a row
    for cl in session.changelistPool:
        
        if session.usernameSpecifiedThroughCmd and cl.developer != session.username:
            continue

        if session.changelist and cl.value != session.changelist:
            continue

        rows.append(SetupsViewRow(cl, session.setupsPool))

    return rows

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Fetch setups')

    formatArg = parser.add_mutually_exclusive_group()
    formatArg.add_argument('--json', action='store_true', default=False, help='Output in JSON format')
    formatArg.add_argument('--csv', action='store_true', default=False, help='Output in CSV format')

    parser.add_argument('--all', action='store_true', default=False, help='Show all changelists')

    args, _ = parser.parse_known_args()

    session = SessionInfo()

    if not session.version:
        print('Cannot get setups without specifying -v [VERSION]', file=sys.stderr)
        exit(1)

    if args.json:
        buildJobs: dict = GqafRequestHandler.fetchSetupsJson(session.version)

        if buildJobs is None:
            print('Failed to fetch setups', file=sys.stderr)
            exit(1)

        print(json.dumps(buildJobs, indent=4), file=sys.stdout)
        session.close()
        exit(0)

    rows: List[SetupsViewRow] = setupsRowsFromSession(session, (20 if not args.all else None))
    printObjectList(rows, csv=args.csv)
    session.close()
    exit(0)