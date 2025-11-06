
from EnvSync.GlobalEnv import GlobalEnv, ConfigScope
from EnvSync.utils import cli
import sys, os

class Color:

    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

def printColored(text: str, color: Color, file = sys.stdout):

    RESET_CODE = '\033[0m'
    print(f'{color}{text}{RESET_CODE}', file=file)

def assertSuccessful(command: str, workingDir: str, verbose: bool = True):

    print(f'\n[CMD] {command}')
    result = cli.runCommand(command, workingDir=workingDir)

    if verbose and result.stderr.strip():
        resultStderr: str = result.stderr.strip()
        resultStderr = ''.join('\t' + line + '\n' for line in resultStderr.splitlines())
        print(resultStderr)

    if result.returncode != 0:
        printColored(f'[RED] {command}', Color.RED)
        sys.exit(result.returncode)

    printColored(f'[ OK] {command}', Color.GREEN)

def runAllPythonFilesInFolder(folderPath: str):

    for file in os.listdir(folderPath):

        if not file.endswith('.py'):
            continue

        filePath = os.path.join(folderPath, file)
        assertSuccessful(f'python {filePath}', workingDir=folderPath, verbose=False)

def runConfigScopeUnitTests():
    assert (ConfigScope.MUREX | ConfigScope.LAPTOP) == 3

def printCurrentScope():
    print('[INFO] Current config scope includes:')

    for scope in ConfigScope:
        if scope & GlobalEnv().currentScope:
            print(f'\t- {scope.name}')

if __name__ == '__main__':

    globalEnv = GlobalEnv()

    runConfigScopeUnitTests()

    # python files return code 0
    runAllPythonFilesInFolder(os.path.join(globalEnv.repoSrcPath, 'config'))
    print(end='\n', file=sys.stderr)
    runAllPythonFilesInFolder(os.path.join(globalEnv.repoSrcPath, 'finance'))
    print(end='\n', file=sys.stderr)

    printCurrentScope()

    secondGlobalEnv = GlobalEnv()
    assert globalEnv is secondGlobalEnv, "GlobalEnv is not a singleton!"
    del globalEnv