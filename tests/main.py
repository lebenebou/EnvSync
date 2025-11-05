
from EnvSync.GlobalEnv import GlobalEnv, ConfigScope
from EnvSync.utils import cli
import sys, os

def assertSuccessful(command: str, workingDir: str, verbose: bool = True):

    print(f'[CMD] {command}', file=sys.stderr)
    result = cli.runCommand(command, workingDir=workingDir)

    if verbose and result.stderr.strip():
        resultStderr: str = result.stderr.strip()
        resultStderr = ''.join('\t' + line + '\n' for line in resultStderr.splitlines())
        print(resultStderr, file=sys.stderr)

    assert result.returncode == 0, f"Command failed: {command}"
    print(f'[ OK] {command}', end='\n\n', file=sys.stderr)

def runAllPythonFilesInFolder(folderPath: str):

    print('[INFO] Running some python files...', file=sys.stderr)
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
    print(end='\n', file=sys.stderr)

    del globalEnv