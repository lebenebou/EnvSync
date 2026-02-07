
import sys, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

SRC_DIR = os.path.join(PARENT_DIR, 'src')
sys.path.append(SRC_DIR)

from GlobalEnv import GlobalEnv
from EnvSyncTest import EnvSyncTest
from utils import cli

def getPythonFilesInFolder(folderPath: str) -> list[str]:

    pythonFiles: list[str] = []

    for file in os.listdir(folderPath):

        if not file.endswith('.py'):
            continue

        fullPath = os.path.join(folderPath, file)
        pythonFiles.append(fullPath)

    return pythonFiles

if __name__ == '__main__':

    globalEnv = GlobalEnv()

    tests: list[EnvSyncTest] = []

    pythonFilesInConfig = getPythonFilesInFolder(os.path.join(globalEnv.repoRootPath, 'src', 'config'))
    for file in pythonFilesInConfig:
        tests.append(EnvSyncTest(f'python {file}').asserts(lambda f=file: cli.runCommand(f'python {f}').returncode == 0))

    allSuccessful: bool = EnvSyncTest.runTests(tests)

    if not allSuccessful:
        exit(1)