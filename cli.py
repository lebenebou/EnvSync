
import subprocess
import sys, os

def runDetached(command: str, *, workingDir: str = None):

    if workingDir is None:
        workingDir = os.getcwd()

    subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=workingDir)

def runCommand(command: str, *, workingDir: str = None, muteOutput: bool = False) -> subprocess.CompletedProcess:

    if workingDir is None:
        workingDir = os.getcwd()

    assert os.path.isdir(workingDir), f'cli: Invalid working directory: {workingDir}'
    result = subprocess.run(command, shell=True, text=True, capture_output=True, encoding="latin1", cwd=workingDir)

    if result.returncode != 0 and not muteOutput:
        print(f'[ERROR] while running: {command}', file=sys.stderr)
        print(result.stderr, file=sys.stderr)

    result.stdout = result.stdout.strip()
    result.stderr = result.stderr.strip()
    return result

def commandOutput(command: str) -> str:
    # do not use unless sure that the command will succeed
    return runCommand(command).stdout