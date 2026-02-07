
import sys, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

SRC_DIR = os.path.join(PARENT_DIR, 'src')
sys.path.append(SRC_DIR)

from GlobalEnv import GlobalEnv, ConfigScope
from EnvSyncTest import EnvSyncTest

def globalEnvIsSingleton() -> bool:

    globalEnv = GlobalEnv()
    secondGlobalEnv = GlobalEnv()
    return globalEnv is secondGlobalEnv

if __name__ == '__main__':

    generalConfigTests: list[EnvSyncTest] = [
        EnvSyncTest('ConfigScope bitwise OR').asserts(lambda: (ConfigScope.MUREX | ConfigScope.LAPTOP) == 3),
        EnvSyncTest('GlobalEnv is singleton').asserts(globalEnvIsSingleton),
    ]

    allSuccessful: bool = EnvSyncTest.runTests(generalConfigTests)

    if not allSuccessful:
        exit(1)