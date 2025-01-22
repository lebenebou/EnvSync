
import sys

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

sys.path.append(PARENT_DIR)

from p4Helper import P4Helper
import settings

if __name__ == '__main__':

    VERSION = settings.getCurrentVersion()

    assert 2 == len(list(P4Helper.getChangelists(version=VERSION, limit=2))), 'Specifying limit yields wrong number of changelists'
    assert len(list(P4Helper.getChangelists(version=P4Helper.Build, limit=300))), 'Failed to fetch 300 changelists on build'