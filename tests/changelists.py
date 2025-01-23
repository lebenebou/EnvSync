
import sys

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

sys.path.append(PARENT_DIR)

from p4Helper import P4Helper
import settings

if __name__ == '__main__':

    VERSION = settings.getCurrentVersion()

    versionCls = list(P4Helper.getChangelists(version=VERSION, limit=2))
    buildCls = list(P4Helper.getChangelists(version=P4Helper.Build, limit=300))

    assert 2 == len(versionCls), 'Specifying limit yields wrong number of changelists'
    assert all(not 'mxp4root' in cl.description for cl in buildCls), 'Some changelist xmls were not parsed'
    assert all(int(cl.value) for cl in buildCls), 'Some changelist values are not integers'

    print('All tests passed')