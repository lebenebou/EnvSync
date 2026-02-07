
import sys, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

SRC_DIR = os.path.join(PARENT_DIR, 'src')

sys.path.append(SRC_DIR)
from utils import cli
from GlobalEnv import GlobalEnv

from EnvSyncTest import EnvSyncTest, printColored, Color

def sshAuthIsWorking() -> bool:

    globalEnv = GlobalEnv()

    numberOfSshAgents = int(cli.commandOutput('ps aux | grep ssh.*agent | wc -l').strip())
    if numberOfSshAgents != 1:
        printColored(f'[WARN] Expected 1 ssh-agent process, found {numberOfSshAgents}', Color.YELLOW, file=sys.stderr)

    result = cli.runCommand('ssh -T git@github.com', workingDir=globalEnv.repoRootPath, muteOutput=True)
    return result.returncode == 1  # GitHub returns 1 for successful auth with no shell access

if __name__ == '__main__':

    sshAuthTests: list[EnvSyncTest] = [
        EnvSyncTest('SSH authentication to GitHub').asserts(sshAuthIsWorking),
    ]

    allSuccessful: bool = EnvSyncTest.runTests(sshAuthTests)

    if not allSuccessful:
        exit(1)