
import argparse
import sys
import json

from GqafRequestHandler import GqafRequestHandler, printObjectList, DeploymentJob
from SessionInfo import SessionInfo

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Fetch deployment jobs')
    parser.add_argument('--json', action='store_true', default=False, help='Output in JSON format')
    parser.add_argument('--latest', action='store_true', default=False, help='Get latest CL with jobs')

    args, _ = parser.parse_known_args()

    session = SessionInfo()

    if not session.version:
        print('Cannot get deployment jobs without specifying version', file=sys.stderr)
        exit(1)
        
    if args.json:
        jobs: dict = GqafRequestHandler.fetchDeploymentJobsJson(session.version)

        if jobs is None:
            print('Failed to fetch jobs', file=sys.stderr)
            exit(1)

        print(json.dumps(jobs, indent=4), file=sys.stdout)
        exit(0)

    ownerFilter = session.username if session.usernameSpecifiedThroughCmd else None
    jobs: list[DeploymentJob] = GqafRequestHandler.fetchDeploymentJobs(session.version, session.changelist, ownerFilter)

    if jobs is None:
        print('Failed to fetch jobs', file=sys.stderr)
        exit(1)

    if args.latest:
        jobs = GqafRequestHandler.filterOnLatestChangelist(jobs)
        
    printObjectList(jobs)
    exit(0)
