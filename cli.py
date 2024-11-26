
import subprocess
import sys

def runDetached(command: str):
    subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)

def runCommand(command: str) -> subprocess.CompletedProcess:

    result = subprocess.run(command, shell=True, text=True, capture_output=True, encoding="latin1")

    if result.returncode != 0:
        print(f'Error while running command: {command}', file=sys.stderr)
        print(result.stderr, file=sys.stderr)

    result.stdout = result.stdout.strip()
    result.stderr = result.stderr.strip()
    return result

def commandOutput(command: str) -> str:
    # do not use unless sure that the command will succeed
    return runCommand(command).stdout