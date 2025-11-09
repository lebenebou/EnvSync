
import subprocess
import sys
import os

def runDetached(command: str):

    subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)

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

def commandOutput(command: str, workingDir: str = None) -> str: return runCommand(command, workingDir = workingDir).stdout

if __name__ == "__main__":

    result = runCommand("echo Hello World!", workingDir=os.getcwd())

    print(f"Output: {result.stdout}")
    print(f"Errors: {result.stderr}")
    print(f"Return code: {result.returncode}")