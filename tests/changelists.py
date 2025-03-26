
import sys

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

sys.path.append(PARENT_DIR)

from SessionInfo import SessionInfo
from p4Helper import P4Helper

if __name__ == '__main__':

    emptyCls = list(P4Helper.getChangelists(P4Helper.Build, developer='non_existant'))
    assert len(emptyCls) == 0, 'non_existant user has changelists on build'

    session = SessionInfo()
    VERSION = session.version

    versionCls = list(P4Helper.getChangelists(version=VERSION, limit=2))
    buildCls = list(P4Helper.getChangelists(version=P4Helper.Build, limit=100))

    assert 2 == len(versionCls), 'Specifying limit yields wrong number of changelists'
    assert all(not 'mxp4root' in cl.description for cl in buildCls), 'Some changelist xmls were not parsed'
    assert all(int(cl.value) for cl in buildCls), 'Some changelist values are not integers'

    # check if fetching files crashes
    print(f'Fetching affected files for some changelists on {P4Helper.Build}...', file=sys.stderr)
    [cl.fetchAffectedFiles() for cl in buildCls]

    print(f'Checking if any files are empty...', file=sys.stderr)
    for cl in buildCls:
        assert all(file for file in cl.files), 'Some fetched affected files are empty or null!'

    print('All tests passed')
    session.close()