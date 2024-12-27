
import argparse
import sys
import json

from typing import List
from GqafRequestHandler import GqafRequestHandler, printObjectList, DeploymentJob
from SessionInfo import SessionInfo

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Fetch deployment jobs')
    parser.add_argument('--json', action='store_true', default=False, help='Output in JSON format')

    args, _ = parser.parse_known_args()

    session = SessionInfo()

    if not session.version:
        print('Cannot get deployment jobs without specifying -v [VERSION]', file=sys.stderr)
        exit(1)
        
    if args.json:
        jobs: dict = GqafRequestHandler.fetchDeploymentJobsJson(session.version)

        if jobs is None:
            print('Failed to fetch jobs', file=sys.stderr)
            exit(1)

        print(json.dumps(jobs, indent=4), file=sys.stdout)
        exit(0)

    ownerFilter = session.username if session.usernameSpecifiedThroughCmd else None
    jobs: List[DeploymentJob] = GqafRequestHandler.fetchDeploymentJobs(session.version, session.changelist, ownerFilter)

    if jobs is None:
        print('Failed to fetch jobs', file=sys.stderr)
        exit(1)

    printObjectList(jobs)
    session.close()