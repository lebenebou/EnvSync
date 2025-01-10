
import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

import cli
import re

import xml.etree.ElementTree as xmlParser
from typing import List

import argparse
from enum import Enum

class Changelist:
    pattern = r'^Change\s+(\d+).*\s+by\s+(\S+)@\S+$'
    defectPattern = r"\[(DEF\d+)\]"

    def __init__(self, value: int):
        self.value = int(value)
        self.defect = None
        self.description = None
        self.developer = None

    def __str__(self) -> str:
        return f'CL {self.value} by {self.developer} - [{self.defect}]{self.description}'

    def __repr__(self) -> str:
        return str(self.value)

    def __eq__(self, other):
        
        if isinstance(other, int):
            return self.value == other

        if not isinstance(other, Changelist):
            return False

        return self.value == other.value
        
    def parseDescription(self, verbose: bool = False):

        assert self.description, f'No description to parse for CL: {self.value}'
        self.description = self.description.strip()

        if '<mxp4Root>' in self.description:
            return self.parseXmlDescription(verbose)

        m = re.match(Changelist.defectPattern, self.description)
        if m is None:
            return self

        self.defect = m.group(1)
        self.description = re.sub(Changelist.defectPattern, '', self.description).strip()
        return self

    def parseXmlDescription(self, verbose: bool = False):

        if verbose:
            print(f'Parsing XML for changelist {self.value}...', end=' ', file=sys.stderr)
 
        root = xmlParser.fromstring(self.description)
        self.description = root.find(".//mxp4description").text.strip()
        self.description = re.sub(r'\s+', ' ', self.description)
        self.defect = root.find(".//mxp4defectID").text.strip()

        return self

    def fetchInfoFromServer(self, verbose: bool = False):
        
        assert self.value, 'cannot fetch info without changelist value'

        command: str = f'p4 describe {self.value}'
        result = cli.runCommand(command)

        if verbose:
            print(f'Fetching info for changelist {self.value}.', end=' ', file=sys.stderr)
            print(f'Running command: {command}', file=sys.stderr)

        assert result.returncode == 0

        output: List[str] = result.stdout.splitlines()

        self.description = ''
        startIndex = 0
        while output[startIndex].startswith('Change'):
            startIndex += 1

        endIndex = startIndex
        while not output[endIndex].startswith('Affected files'):
            endIndex += 1

        for i in range(startIndex, endIndex):
            self.description += output[i]

        m = re.search(Changelist.defectPattern, self.description)
        self.defect = m.group(1) if m else None
        self.description = re.sub(Changelist.defectPattern, '', self.description)
        self.description = self.description.strip()

        self.developer = re.search(r'Change \d+.*by (\S+)@', output[0]).group(1)
        return self

class P4Helper:
    Build: str = 'v3.1.build'

    @staticmethod
    def getHeadChangelist(version: str, n: int = 0, verbose: bool = False) -> int:

        if version == None:
            print(f'Can\'t get changelists without specifying version', file=sys.stderr)
            return None

        n = max(0, n)

        command = f'p4 changes -s submitted -m {n+1} {P4Helper.depoVersion(version)}' # limit output to n+1 lines

        if verbose:
            print(f'Getting head changelists for {version}...', end= ' ', file=sys.stderr)
            print(f'Running command: {command}', file=sys.stderr)

        result = cli.runCommand(command)

        if result.returncode != 0 or not result.stdout:
            print(f'Failed to retrieve changelists for version: {version}. Are you sure this is a valid version?', file=sys.stderr)
            return None

        outputLines: str = result.stdout.splitlines()
        clResult: int = None
        for i, line in enumerate(outputLines):

            regexMatch = re.search(r'^change (\d+)', line, re.IGNORECASE)
            assert regexMatch is not None, f'not a "p4 changes" output, CL regex did not match in: {line}'

            clResult = int(regexMatch.group(1))
            if i == 0:
                print(f'Head CL: {clResult}', file=sys.stderr)
                continue

            print(f'Then CL: {clResult}', file=sys.stderr)

        return clResult

    @staticmethod
    def depoVersion(rawVersion: str) -> str:

        if "depot" in rawVersion:
            return rawVersion.strip("/...") + "/..."

        return f"//depot/{rawVersion}/..."

    from typing import Generator
    @staticmethod
    def getChangelists(version: str, developer: str = None, limit: int = None, verbose: bool = False) -> Generator[Changelist, None, None]:

        print(f'Getting changelists on {version}...', end=' ', file=sys.stderr)

        command = 'p4 changes -l -s submitted'

        if limit:
            print(f'(Limiting search to {limit} changelists)', end='', file=sys.stderr)
            command += f' -m {limit}'

        print(end='\n\n', file=sys.stderr, flush=True)

        if developer:
            command += f' -u {developer}'

        command += f' {P4Helper.depoVersion(version)}'

        if verbose:
            print(f'Running command: {command}', file=sys.stderr)

        result = cli.runCommand(command)

        if result.returncode != 0:
            print(f'Failed to get changelists on {version}', file=sys.stderr)
            return []

        output: List[str] = result.stdout.splitlines()

        i = 0
        while i < len(output):

            m = re.match(Changelist.pattern, output[i])

            assert m is not None, 'Couldnt match changelist regex pattern'
            cl = Changelist(m.group(1).strip())
            cl.developer = m.group(2).strip()

            i+=1
            while output[i].strip() == '': i+=1
            cl.description = output[i].strip()

            cl.parseDescription()

            i+=1
            if i >= len(output):
                break
            while output[i].strip() == '': i+=1

            yield cl

    @staticmethod
    def getUnmergredChangelists(src: str, dest: str, developer: str = None, verbose: bool = False) -> List[Changelist]:

        # returns changelists submitted by <developer> that are NOT merged from src to dest, based on defectID

        srcCls = P4Helper.getChangelists(src, developer, limit=None, verbose=verbose)

        destLimit = 200 if dest == P4Helper.Build else None # users might have a large number of changelists submitted to build, 200 should be enough
        destCls = P4Helper.getChangelists(dest, developer, limit=destLimit, verbose=verbose)

        destDefects = set(cl.defect for cl in destCls)

        unmergedCls = [cl for cl in srcCls if cl.defect is not None and cl.defect not in destDefects]

        return unmergedCls

    @staticmethod
    def getUnmergredDefects(src: str, dest: str, developer: str = None, verbose: bool = False) -> List[str]:
        # returns defects submitted by <developer> that are NOT merged from src to dest
        return [cl.defect for cl in P4Helper.getUnmergredChangelists(src, dest, developer, verbose)]

if __name__ == '__main__':

    from SessionInfo import SessionInfo
    session = SessionInfo()

    if not session.version:
        print('No version specified', file=sys.stderr)
        exit(1)

    parser = argparse.ArgumentParser(description='Display changelists')

    parser.add_argument('--unmerged', nargs='?', const=P4Helper.Build, default=None, type=str, help='only changelists which are unmerged (based on defectID)')
    parser.add_argument('--defects', action="store_true", help='display defects instead of changelists')
    parser.add_argument('-l', '--limit', default=None, type=int, help='limit the output to a certain number of changelists')

    args, _ = parser.parse_known_args()

    if args.unmerged is not None:

        unmergedCls = P4Helper.getUnmergredChangelists(session.version, args.unmerged, session.username, session.verbose)

        if len(unmergedCls) == 0:
            print(f'{session.username} has merged all his defects from {session.version} to {args.unmerged}', file=sys.stderr)
            session.close()
            exit(0)

        if args.defects:
            print(f'{session.username}\'s defects on {session.version} not yet on {args.unmerged}:', file=sys.stderr)
            print(', '.join(set(cl.defect for cl in unmergedCls)))
            session.close()
            exit(0)

        print(f'{session.username}\'s Cls on {session.version} not yet on {args.unmerged}:', file=sys.stderr)
        [print(cl) for cl in unmergedCls]
        session.close()
        exit(0)

    usernameFilter = (session.username if session.usernameSpecifiedThroughCmd else None)
    [print(cl) for cl in P4Helper.getChangelists(session.version, usernameFilter, args.limit, session.verbose)]
    session.close()
    exit(0)