
import argparse
import settings
import sys

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

from p4Helper import P4Helper, Changelist
from typing import Dict, List

def isValidVersion(version: str) -> bool:

    if not version.startswith('v3.1.'):
        return False

    return True

class SessionInfo:

    def __init__(self, forceVerbose: bool = False):
        
        parser = argparse.ArgumentParser(description='Parse the arguments of a Murex SessionInfo', add_help=True)

        versionArg = parser.add_mutually_exclusive_group(required=False)
        versionArg.add_argument("-v", "--version", type=str, required=False)
        versionArg.add_argument("--build", action="store_true", required=False)

        usernameArg = parser.add_mutually_exclusive_group(required=False)
        usernameArg.add_argument("-u", "--username", type=str)
        usernameArg.add_argument("--me", action="store_true", required=False)

        clArg = parser.add_mutually_exclusive_group(required=False)
        clArg.add_argument('-cl', '--changelist', type=int, required=False)
        clArg.add_argument('--head', nargs='?', const=0, default=None, type=int, help='Head CL minus N (--head 1 is CL just before head)')
        clArg.add_argument('--latest', action="store_true", help='Latest CL with Linux setups')

        parser.add_argument("--verbose", action="store_true", required=False)

        args, _ = parser.parse_known_args()

        self.setupsPool: Dict[int, List] = None
        self.changelistPool: List[Changelist] = None

        # Verbose
        self.verbose = args.verbose
        if forceVerbose:
            self.verbose = True

        # Version
        self.version = settings.getCurrentVersion()

        if args.version:
            self.version = args.version

        if args.build:
            self.version = P4Helper.Build

        # Changelist
        self.changelist: int = None
        if args.changelist:
            self.changelist = args.changelist

        elif args.head is not None:
            self.changelist = P4Helper.getHeadChangelist(self.version, args.head, self.verbose)

        elif args.latest:

            self.setChangelistToLatestWithSetups()
            if self.changelist is not None:
                print(f'Latest linux setups are on {self.changelist}', file=sys.stderr)

        # Username
        self.username: str = settings.getUsername()

        if args.username:
            self.username = args.username
        if args.me:
            self.username = settings.getUsername()

        self.usernameSpecifiedThroughCmd = bool(args.username or args.me)

        self.checkSanity()

        if self.verbose:
            print('\nParsed session info:', file=sys.stderr)
            print(self, file=sys.stderr)

    def __str__(self) -> str:

        tmpDict = dict(self.__dict__)

        tmpDict.pop('setupsPool')
        tmpDict.pop('changelistPool')

        tmpDict['SetupsPool'] = 0 if self.setupsPool is None else len(self.setupsPool.keys())
        tmpDict['ChangelistPool'] = 0 if self.changelistPool is None else len(self.changelistPool)

        return tmpDict.__str__().replace('\n', ' ').replace('\'', '')

    def checkSanity(self):

        assert isValidVersion(self.version), f'Invalid version name: {self.version}'

        assert self.changelist is None or self.changelist > 100, f'Invalid changelist: {self.changelist}'

        assert self.username is None or self.username != '', f'Username is empty'
        assert all(not c.isdigit() for c in self.username), f'Username has numbers: {self.username}'

    def fetchChangelistPool(self, lazy: bool = True, limit: int = None) -> Dict[int, List]:

        if lazy and self.changelistPool is not None and len(self.changelistPool) >= limit:
            return self.changelistPool

        if not self.version:
            print(f'Cannot get changelists without specifying version', file=sys.stderr)
            self.changelistPool = None
            return

        self.changelistPool = list(P4Helper.getChangelists(version=self.version, verbose=self.verbose, limit=limit))
        
    def fetchSetupsPool(self, lazy: bool = True) -> Dict[int, List]:

        from gqaf.GqafRequestHandler import GqafRequestHandler, BuildJob

        if lazy and self.setupsPool is not None:
            return self.setupsPool

        buildJobs = GqafRequestHandler.fetchBuildJobs(self.version)
        self.setupsPool: Dict[int, List[BuildJob]] = {}

        for build in buildJobs:
            self.setupsPool.setdefault(build.changelist, []).append(build)

        return self.setupsPool

    def setChangelistToLatestWithSetups(self):

        if not self.version:
            print(f'Cannot get latest setups without specifying version', file=sys.stderr)
            self.changelist = None
            return

        self.fetchSetupsPool(lazy=True)

        # starting with most recent cl, find available setups
        self.fetchChangelistPool(lazy=True)
        for cl in self.changelistPool:

            if cl.value not in self.setupsPool:
                continue

            for build in self.setupsPool[cl.value]:

                if build.isDone() and build.isLinux():
                    self.changelist = cl.value
                    return

        self.changelist = None
        return

if __name__ == '__main__':
    session = SessionInfo(forceVerbose=True)