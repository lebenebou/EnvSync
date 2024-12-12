
import argparse
import sys
import os
from typing import List
import re

import asyncio

from GqafRequestHandler import GqafRequestHandler, DeploymentJobInput, BuildJob
from SessionInfo import SessionInfo

def readFileLines(filePath: str) -> List[str]:

    assert os.path.isfile(filePath), f'Not a file: {filePath}'

    with open(filePath, 'r') as file:
        return file.readlines()

def readStdinLines() -> List[str]:

    print(f"reading from stdin...", file=sys.stderr)
    return sys.stdin.read().splitlines()

def parseJobInputsFromLines(lines: List[str], verbose: bool = False) -> List[DeploymentJobInput]:

    pattern = re.compile(r'TPK\S(\d+)\s.*?(\S{3,})')

    inputs: List[DeploymentJobInput] = []

    if verbose:
        print(f"Parsing jobs from input...", file=sys.stderr)

    for line in lines:

        m = pattern.search(line)
        if not m:
            continue

        input = DeploymentJobInput()

        package = m.group(1) # 1567
        while len(package) < 7: package = f'0{package}' # 0001567
        input.testPackage = f'PAR.TPK.{package}' # PAR.TPK.0001567

        input.nickname = m.group(2)

        if verbose:
            print(f"Found: {input.testPackage} - {input.nickname}", file=sys.stderr)

        inputs.append(input)
        continue

    if verbose:
        print(f"{len(inputs)} job(s) parsed from input", file=sys.stderr)

    return inputs

def getLinuxSetupsAtCl(version: str, changelist: int) -> BuildJob:

    validSetups = GqafRequestHandler.fetchBuildJobs(version, changelist)
    validSetups = [b for b in validSetups if 'linux' in b.operatingSystem.lower() and b.status == 'DONE']

    if len(validSetups) == 0:
        return None

    return validSetups[0]

def fillJobInputs(inputs: List[DeploymentJobInput], session: SessionInfo, cliArgs: any):

    for input in inputs:
        
        input.version = session.version
        input.versionValidationId = GqafRequestHandler.getVersionValidationAtok(session.version)

        if cliArgs.keep:
            input.keepIfFailed = True

        if cliArgs.wait:
            input.waitingBuildId = input.buildId
            input.buildId = None

        continue

async def pushJob(input: DeploymentJobInput) -> dict: # returns the input with an extra parJobId field

    loop = asyncio.get_event_loop()
    parDjobId = await loop.run_in_executor(None, GqafRequestHandler.pushDeploymentJob, input)

    pushedJobInfo = input.toJson()
    pushedJobInfo['parJobId'] = parDjobId

    print(f'{input}:\t\t\t{parDjobId}')
    return pushedJobInfo

async def main():

    parser = argparse.ArgumentParser(description='Push deployment job(s) by reading from stdin')

    parser.add_argument('file_to_parse', nargs='?', default=None, help='File to parse PAR.TPKs from, otherwise parse from stdin')

    parser.add_argument('--buildId', type=str, help='Build Id on which the job will be pushed', required=False)
    parser.add_argument('--wait', action='store_true', default=False, help='wait for the given buildId', required=False)
    parser.add_argument('--keep', action='store_true', default=False, help='keep job if failed', required=False)

    args, _ = parser.parse_known_args()

    session = SessionInfo()

    if session.version is None:
        print(f"Cannot push job without a version", file=sys.stderr)
        exit(1)

    chosenBuildId: str = None
    if args.buildId:
        chosenBuildId = args.buildId

    elif session.changelist:

        latestSetups = getLinuxSetupsAtCl(session.version, session.changelist)
        if latestSetups is None:
            print(f"No setups on changelist {session.changelist}.", file=sys.stderr)
            exit(1)

        chosenBuildId = latestSetups.buildId

    if not chosenBuildId:
        print(f"Cannot push job without buildId or CL", file=sys.stderr)
        exit(1)

    linesToParse: List[str] = []
    if args.file_to_parse:

        fileToParse: str = args.file_to_parse.strip()

        if not os.path.exists(fileToParse):
            print(f'Path does not exist: {fileToParse}')
            exit(1)

        if not os.path.isfile(fileToParse):
            print(f'Not a file: {fileToParse}')
            exit(1)

        linesToParse = readFileLines(fileToParse)
    else:
        linesToParse = readStdinLines()

    jobsToPush: List[DeploymentJobInput] = parseJobInputsFromLines(linesToParse, session.verbose)
    [job.setBuildId(chosenBuildId) for job in jobsToPush]

    if len(jobsToPush) == 0:
        print(f'\nNo jobs were parsed. DISCLAMER: jobs are parsed line by line. Here are some examples:', file=sys.stderr)
        print(f'PAR.TPK.0002077 - DEFAULT_1', file=sys.stderr)
        print(f'PAR.TPK.0001681 BOND', file=sys.stderr)
        exit(1)

    fillJobInputs(jobsToPush, session, args)

    pushedJobs = await asyncio.gather(*(pushJob(j) for j in jobsToPush))

    exitCode = 0 if any(job.get('parJobId') for job in pushedJobs) else 1
    return exitCode

if __name__ == '__main__':

    PYTHON_VERSION = sys.version_info

    if PYTHON_VERSION >= (3, 7):
        exitCode = asyncio.run(main())
        exit(exitCode)

    # for versions lower than 3.7:
    loop = asyncio.get_event_loop()

    try:
        exitCode = loop.run_until_complete(main())
    finally:
        loop.close()

    exit(exitCode)