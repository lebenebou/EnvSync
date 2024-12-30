
import argparse
import sys
import json

from typing import List, Dict
from GqafRequestHandler import GqafRequestHandler, printObjectList, BuildJob
from SessionInfo import SessionInfo
from p4Helper import Changelist

class SetupsViewRow:

    def __init__(self, changelist: Changelist, setupsPool: Dict[int, List[BuildJob]]):
        
        self.deployer = None
        self.developer = changelist.developer
        self.changelist = changelist.value

        self.windows = '-----'
        self.linux = '-----'
        self.linuxBuildId = '-----'

        bestLinuxBuild: BuildJob = None
        bestWindowsBuild: BuildJob = None

        for build in setupsPool.get(changelist.value, dict()):

            if build.isLinux():
                bestLinuxBuild = SetupsViewRow.moreRelevantBuild(bestLinuxBuild, build)

            elif build.isWindows():
                bestWindowsBuild = SetupsViewRow.moreRelevantBuild(bestWindowsBuild, build)

        if bestLinuxBuild:
            self.linux = bestLinuxBuild.status
            self.linuxBuildId = bestLinuxBuild.buildId
            self.deployer = bestLinuxBuild.deployer

        if bestWindowsBuild:
            self.windows = bestWindowsBuild.status

        self.description = f'[{changelist.defect}]{changelist.description}'
        return

    @staticmethod
    def moreRelevantBuild(b1: BuildJob, b2: BuildJob):

        if b1 is None or b2 is None:
            return b1 if b1 else b2

        if b1.status == b2.status:
            return b1 if b1.deployDate > b2.deployDate else b2 # more recent build

        statusPriority = ('DONE', 'TAKEN', 'FAILED', 'STOPPED', 'PURGED')
        for status in statusPriority:

            if status in (b1.status, b2.status):
                return b1 if b1.status == status else b2

        return b2

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Fetch setups')

    parser.add_argument('--json', action='store_true', default=False, help='Output in JSON format')
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

    session.fetchChangelistPool(lazy=True, limit = (20 if not args.all else None) )
    session.fetchSetupsPool(lazy=True)

    rows: List[SetupsViewRow] = [] # for each changelist in ascending order, get the most relevant build job and add it as a row
    for cl in session.changelistPool:
        
        if session.usernameSpecifiedThroughCmd and cl.developer != session.username:
            continue

        if session.changelist and cl.value != session.changelist:
            continue

        rows.append(SetupsViewRow(cl, session.setupsPool))

    printObjectList(rows)
    session.close()
    exit(0)