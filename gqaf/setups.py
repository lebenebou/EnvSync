
import argparse
import sys
import json

from GqafRequestHandler import GqafRequestHandler, printObjectList, BuildJob
from SessionInfo import SessionInfo

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Fetch setups')
    parser.add_argument('--json', action='store_true', default=False, help='Output in JSON format')
    parser.add_argument('--latest', action='store_true', default=False, help='Get latest Cl with setups')

    args, _ = parser.parse_known_args()

    session = SessionInfo()

    if not session.version:
        print('Cannot get setups without specifying version', file=sys.stderr)
        exit(1)
        
    if args.json:
        buildJobs: dict = GqafRequestHandler.fetchDeploymentJobsJson(session.version)

        if buildJobs is None:
            print('Failed to fetch setups', file=sys.stderr)
            exit(1)

        print(json.dumps(buildJobs, indent=4), file=sys.stdout)
        exit(0)

    ownerFilter = session.username if session.usernameSpecifiedThroughCmd else None
    buildJobs: list[BuildJob] = GqafRequestHandler.fetchBuildJobs(session.version, session.changelist, ownerFilter)

    if buildJobs is None:
        print('Failed to fetch setups', file=sys.stderr)
        exit(1)
     
    if args.latest:
        buildJobs = GqafRequestHandler.filterOnLatestChangelist(buildJobs)
        
    printObjectList(buildJobs)
    exit(0)
