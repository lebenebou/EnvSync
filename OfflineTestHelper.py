
import settings
from SessionInfo import SessionInfo

import re
import os

if __name__ == '__main__':

    session = SessionInfo()

    VS_PROJECTS_PATH: str = os.path.join('D:', session.version, '_projects')
    projectName: str = 'libcpp_mxftest_lie'
    PROJECT_CONFIG_XML_PATH: str = os.path.join(VS_PROJECTS_PATH, projectName + '.vcxproj.user')

    assert(os.path.isfile(PROJECT_CONFIG_XML_PATH))