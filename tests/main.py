
from EnvSync.GlobalEnv import GlobalEnv
from EnvSync.utils import cli
import sys, os

def assertSuccessful(command: str, workingDir: str):

    print(f'Running: {command}', file=sys.stderr)
    result = cli.runCommand(command, workingDir=workingDir)
    assert result.returncode == 0, f"Command failed: {command}"

def runAllPythonFilesInFolder(folderPath: str):

    for file in os.listdir(folderPath):

        if not file.endswith('.py'):
            continue

        filePath = os.path.join(folderPath, file)
        assertSuccessful(f'python "{filePath}"', workingDir=folderPath)

if __name__ == '__main__':

    globalEnv = GlobalEnv()

    # python files return code 0
    runAllPythonFilesInFolder(os.path.join(globalEnv.repoSrcPath, 'config'))
    runAllPythonFilesInFolder(os.path.join(globalEnv.repoSrcPath, 'finance'))