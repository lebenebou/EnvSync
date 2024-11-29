
import argparse
import settings
import sys

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

from p4Helper import P4Helper

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
            from gqaf.GqafRequestHandler import GqafRequestHandler

            if self.verbose:
                print(f'Getting latest linux setups for {self.version}...', file=sys.stderr)

            if not self.version:
                print(f'Cannot get latest setups without specifying version', file=sys.stderr)
                self.changelist = None

            else:
                latestSetups = GqafRequestHandler.getLatestLinuxSetups(self.version)
                self.changelist = latestSetups.changelist

                if self.changelist:
                    print(f'Latest linux setups are on {self.changelist}', file=sys.stderr)
                else:
                    print(f'No linux setups on {self.version}', file=sys.stderr)

        # Username
        self.username = settings.getUsername()

        if args.username:
            self.username = args.username
        if args.me:
            self.username = settings.getUsername()

        self.usernameSpecifiedThroughCmd = bool(args.username or args.me)

        if self.verbose:
            print('\nParsed session info:', file=sys.stderr)
            print(self.__dict__.__str__().replace('\n', ' ').replace('\'', ''))

if __name__ == '__main__':

    session = SessionInfo(forceVerbose=True)