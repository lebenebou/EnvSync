
import argparse
import sys
import json

from GqafRequestHandler import GqafRequestHandler, printObjectList
from SessionInfo import SessionInfo
from RichVersionView import RichVersionView, createSetupsView

def setupsRowsFromSession(session: SessionInfo, limit: int = 20):

    setupsRichView: RichVersionView = createSetupsView(session.fetchSetupsPool(lazy=True))
    return setupsRichView.buildRows(session.fetchChangelistPool(lazy=True, limit=limit))

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

    rows = setupsRowsFromSession(session, (20 if not args.all else None))
    printObjectList(rows, csv=args.csv)
    session.close()
    exit(0)