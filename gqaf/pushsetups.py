
import argparse
import sys

import json

from GqafRequestHandler import GqafRequestHandler, BuildJobInput
from SessionInfo import SessionInfo

if __name__ == '__main__':

    parser = argparse.ArgumentParser('Push a build job')

    # Cls
    parser.add_argument('--shelved-cl', type=int)

    # OS
    osArgs = parser.add_argument_group(description='OS to push setups on')
    osArgs.add_argument('--linux', action='store_true', default=False, help='Linux-rhel-8.6-x86_64')
    osArgs.add_argument('--windows', action='store_true', default=False, help='Windows-x86-5.2-64b')

    # Customization
    customizationArgs = parser.add_argument_group(description='Customization')
    customizationArgs.add_argument('--force', action='store_true', default=False, help='Force setups')
    customizationArgs.add_argument('--mts', action='store_true', default=False, help='MTS version')

    args, _ = parser.parse_known_args()

    session = SessionInfo()

    if session.changelist is None:
        print(f"Cannot push setups without a -cl [CHANGELIST]", file=sys.stderr)
        exit(1)

    if args.linux==False and args.windows==False:
        print(f"No operating system(s) chosen: [--linux | --windows]", file=sys.stderr)
        exit(1)

    # Build input
    input = BuildJobInput()

    input.owner = session.username
    input.version = session.version
    input.changelist = session.changelist
    input.shelvedChangelists = [args.shelved_cl] if args.shelved_cl else []
    input.force = bool(args.force)
    input.mts = bool(args.mts)

    if args.linux:
        input.operatingSystems.append('linux')

    if args.windows:
        input.operatingSystems.append('windows')

    # Try to push setups
    commandId: int = GqafRequestHandler.pushBuildJob(input)
    if commandId is None:
        print(f"Couldn't push setups.", file=sys.stderr)
        exit(1)

    print(f'Setups pushed.', file=sys.stderr)

    pushedSetupsInfo = input.toJson()
    pushedSetupsInfo['commandId'] = commandId

    print(json.dumps(pushedSetupsInfo, indent=4), file=sys.stdout)
    session.close()
    exit(0)