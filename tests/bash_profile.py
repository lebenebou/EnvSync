
import sys, os
import time

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

SRC_DIR = os.path.join(PARENT_DIR, 'src')
sys.path.append(SRC_DIR)

from EnvSyncTest import EnvSyncTest
from GlobalEnv import GlobalEnv

from utils import cli

BASH_PROFILE_PY = os.path.join(GlobalEnv().repoSrcPath, 'config', 'BashProfile.py')

def pythonScriptGeneratesCorrectSyntax() -> bool:

    result = cli.runCommand(f'python "{BASH_PROFILE_PY}" | bash -n', workingDir=GlobalEnv().repoRootPath)
    return result.returncode == 0

def homeBashProfileHasCorrectSyntax() -> bool:

    homeBashProfile: str = os.path.join(GlobalEnv().getBashProfilePath())

    result = cli.runCommand(f'bash -n "{homeBashProfile}"', workingDir=GlobalEnv().repoRootPath)
    return result.returncode == 0

if __name__ == '__main__':

    tests: list[EnvSyncTest] = [
        EnvSyncTest('BashProfile.py generates correct bash syntax').asserts(pythonScriptGeneratesCorrectSyntax),
        EnvSyncTest('Home .bash_profile has correct bash syntax').asserts(homeBashProfileHasCorrectSyntax),
    ]

    allSuccessful: bool = EnvSyncTest.runTests(tests)

    if not allSuccessful:
        exit(1)