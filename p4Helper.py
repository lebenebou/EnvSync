
import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

import cli
import re

import xml.etree.ElementTree as xmlParser
from typing import List, Dict

import argparse

class Changelist:
    pattern = r'^Change\s+(\d+).*\s+by\s+(\S+)@'
    tagPattern = r"\[\s*(.*?)\s*]"

    def __init__(self, value: int = 0):

        self.value = int(value)
        self.defect = None
        self.description = None
        self.tags: List[str] = []
        self.developer = None

        self.files: List[str] = []

        self.gitCommit: str = None

    @staticmethod
    def fromP4CmdOutput(outputLines: List[str], startIndex: int = 0):

        # INPUT: p4 command output, and a start index
        # OUTPUT: tuple of (parsed Changelist , index of next changelist in the output)

        i: int = startIndex
        m = re.match(Changelist.pattern, outputLines[i])
        assert m, f'Line did not match changelist regex: {outputLines[i]}'

        cl = Changelist()
        cl.value, cl.developer = m.groups()

        i += 2
        cl.description = ''

        while True:

            cl.description += outputLines[i] 
            i+=1

            endOfOutput: bool = (i >= len(outputLines))
            if endOfOutput:
                return (cl, -1)

            atNextClOutput: bool = outputLines[i].startswith('Change')
            if atNextClOutput:
                return (cl, i)

            if outputLines[i].startswith('Affected'):

                i += 2
                while i < len(outputLines) and not re.match(r'^\s*$', outputLines[i]):
                    file: str = P4Helper.parsePathFromDepoPath(outputLines[i])
                    cl.files.append(file)
                    i += 1

                return (cl, -1)

    def fetchAffectedFiles(self, verbose: bool = False) -> List[str]:

        if self.developer == 'builder':
            print(f'Skipped fetching files for "builder" user: CL {self.value}', file=sys.stderr)
            return []

        if self.files:
            return self.files

        command = f'p4 describe {self.value}'
        if verbose:
            print(f'Fetching affected files for changelist {self.value} (command: {command})', file=sys.stderr)

        result = cli.runCommand(command)
        if result.returncode != 0:
            print(f'p4 describe {self.value} failed, could not retrieve files for this changelist', file=sys.stderr)
            return []

        output: List[str] = result.stdout.splitlines()
        tmpCL, _ = Changelist.fromP4CmdOutput(output)

        self.files = list(tmpCL.files)
        return self.files

    def isCherryPickedFromGit(self) -> bool:
        return self.gitCommit is not None

    def toString(self, onlyTags: bool = False, withFiles: bool = False) -> str:

        s: str = f'CL {self.value} by {self.developer}'
        s += ' - '
        s += f'[{self.defect}]'

        s += self.allTags()

        if not onlyTags:
            s += f' {self.description}'

        if withFiles:
            self.fetchAffectedFiles()
            s += '\n\t'
            s += '\n\t'.join(self.files)
            s += '\n'

        return s.encode('ascii', errors='ignore').decode('ascii')

    def allTags(self, withDefect: bool = False) -> str:

        s = str()

        if withDefect and self.defect:
            s += f'[{self.defect}]'

        for tag in self.tags:
            s += f'[{tag}]'

        return s

    def __str__(self) -> str:
        return self.toString()

    def __repr__(self) -> str:
        return str(self.value)

    def __eq__(self, other):
        
        if isinstance(other, int):
            return self.value == other

        if not isinstance(other, Changelist):
            return False

        return self.value == other.value
        
    def parseAndCleanDescription(self, verbose: bool = False):

        assert self.description, f'No description to parse for CL: {self.value}'

        if verbose:
            print(f'Parsing description for changelist {self.value}...', file=sys.stderr)

        self.description = self.description.strip()
        self.description = self.description.replace('\n', ' ')

        self.value = int(self.value)

        if self.description.startswith('<mxp4Root>'):
            self.parseXmlDescription(verbose)

        # parse [tags]
        for m in re.finditer(Changelist.tagPattern, self.description):

            matchstr = m.group(1).strip()

            if re.match(P4Helper.DefectRegex, matchstr):
                self.defect = matchstr
            else:
                self.tags.append(matchstr)

        # remove [tags]
        self.description = re.sub(Changelist.tagPattern, '', self.description).strip()

        # remove (cherry picked from commit X)...
        gitCommitPattern: str = r'\(cherry\s+picked\s+from\s+commit\s+(\S+)\).*'
        m = re.search(gitCommitPattern, self.description)
        if m:
            self.gitCommit = m.group(1)
            self.description = re.sub(gitCommitPattern, '', self.description).strip()

        gitCommitPattern: str = r'Changelist\s*generated\s*by.*Git.*Commit-id:\s*(\S+).*'
        m = re.search(gitCommitPattern, self.description)
        if m:
            self.gitCommit = m.group(1)
            self.description = re.sub(gitCommitPattern, '', self.description).strip()

        # remove double spaces
        self.description = self.description.replace('  ', ' ')

        return self

    def parseXmlDescription(self, verbose: bool = False):

        if verbose:
            print(f'Parsing XML for changelist {self.value}...', file=sys.stderr)
 
        root = xmlParser.fromstring(self.description)
        self.description = root.find(".//mxp4description").text.strip()
        self.description = re.sub(r'\s+', ' ', self.description) # remove double spaces
        self.defect = root.find(".//mxp4defectID").text.strip()

        return self

class P4Helper:
    Build: str = 'v3.1.build'
    DefectRegex: str = r'DEF\d+'

    @staticmethod
    def depoVersion(rawVersion: str) -> str:

        if "depot" in rawVersion:
            return rawVersion.strip("/...") + "/..."

        return f"//depot/{rawVersion}/..."

    @staticmethod
    def parsePathFromDepoPath(depoPath: str) -> str:

        depoPath = depoPath.strip(' ').strip('.').strip(' ')
        pattern = r'depot/v3\.1\.\S+?/(.*)#'
        m = re.search(pattern, depoPath)

        if not m:
            return None

        file = m.group(1)
        return file

    @staticmethod
    def _getChangelist(changelist: int, verbose: bool = False) -> Changelist:

        command = f'p4 describe -s {changelist}'

        if verbose:
            print(f'Running command: {command}', file=sys.stderr)

        result = cli.runCommand(command)

        if result.returncode != 0:
            print(f'Failed to get changelist: {changelist}', file=sys.stderr)
            return None

        if not result.stdout:
            print(result.stderr, file=sys.stderr)
            return None

        cl, _ = Changelist.fromP4CmdOutput(result.stdout.splitlines())
        cl.parseAndCleanDescription(verbose)
        return cl
        
    @staticmethod
    def extractMainstreamDefects(defects: List[str], possibleSubmitters: List[str]) -> Dict[str, Changelist]:

        # INPUT
        # Defects: list of defects
        # PossibleSubmitters: list of users

        # OUTPUT
        # dictionary containing the defects as key, and the FIRST changelist which submitted them on v3.1.build as value
        # if the defect is NOT submitted on build by any of the given users, it will NOT be present in the dictionary

        mainstreamDefects: Dict[str, Changelist] = {}
        for dev in possibleSubmitters:

            for cl in P4Helper.getChangelists(P4Helper.Build, developer=dev):

                if cl.defect not in defects:
                    continue

                mainstreamDefects[cl.defect] = cl

        return mainstreamDefects

    from typing import Generator
    @staticmethod
    def getChangelists(version: str, *, developer: str = None, limit: int = None, fileRegex: str = None, verbose: bool = False) -> Generator[Changelist, None, None]:

        print(f'Getting changelists on {version}...', end='', file=sys.stderr)

        command = 'p4 changes -l -s submitted'

        if version == P4Helper.Build and not limit and not developer: # getting all changelists on build takes a lot of time
            limit = 500

        if limit:
            print(f' (Limiting search to {limit} changelists)', end='', file=sys.stderr)
            command += f' -m {limit}'

        print(end='\n', file=sys.stderr, flush=True)

        if developer:
            command += f' -u {developer}'

        command += f' {P4Helper.depoVersion(version)}'

        if verbose:
            print(f'Running command: {command}', file=sys.stderr)

        result = cli.runCommand(command)

        if result.returncode != 0:
            print(f'Failed to get changelists on {version}', file=sys.stderr)
            return []

        changelists: List[Changelist] = []
        outputLines: List[str] = result.stdout.splitlines()

        # Parse the output for changelists and descriptions
        nextClIndex = 0
        while nextClIndex != -1:

            cl, nextClIndex = Changelist.fromP4CmdOutput(outputLines, nextClIndex)
            cl.parseAndCleanDescription()
            changelists.append(cl)

        # at this point we have the chaneglists and their parsed descriptions

        for cl in changelists:

            noFilesMatchRegex: bool = fileRegex and not any(re.search(fileRegex, f, re.IGNORECASE) for f in cl.fetchAffectedFiles(verbose))
            if noFilesMatchRegex:
                continue

            if False: # extensible for more filters in the future
                continue

            yield cl

    @staticmethod
    def getUnmergredChangelists(src: str, dest: str, developer: str = None, verbose: bool = False) -> List[Changelist]:

        # returns changelists submitted by <developer> that are NOT merged from src to dest, based on defectID

        srcCls = P4Helper.getChangelists(version=src, developer=developer, verbose=verbose)
        destCls = P4Helper.getChangelists(version=dest, developer=developer, verbose=verbose)

        destDefects = set(cl.defect for cl in destCls)

        unmergedCls = [cl for cl in srcCls if cl.defect is not None and cl.defect not in destDefects]

        return unmergedCls

if __name__ == '__main__':

    from SessionInfo import SessionInfo
    session = SessionInfo()

    if not session.version:
        print('No version specified', file=sys.stderr)
        exit(1)

    parser = argparse.ArgumentParser(description='Display changelists')

    parser.add_argument('--unmerged', nargs='?', const=P4Helper.Build, default=None, type=str, help='only changelists which are unmerged (based on defectID)')
    parser.add_argument('-l', '--limit', default=None, type=int, help='limit the output to a certain number of changelists')
    parser.add_argument('-f', '--file', type=str, nargs='?', const='.*', default=None, help='output changelit files. if value is given, filter on matching files by regex')

    args, _ = parser.parse_known_args()

    if session.changelist:

        cl = P4Helper._getChangelist(session.changelist, session.verbose)

        if not cl:
            print(f'Could not get changelist: {session.changelist}', file=sys.stderr)
            exit(1)

        print(cl.toString(withFiles=args.file))
        exit(0)

    if args.unmerged is not None:

        if not session.username:
            print(f'Username is required to fetch unmerged changelists', file=sys.stderr)
            exit(1)

        unmergedCls = P4Helper.getUnmergredChangelists(session.version, args.unmerged, session.username, session.verbose)

        if len(unmergedCls) == 0:
            print(f'{session.username} has merged all his defects from {session.version} to {args.unmerged}', file=sys.stderr)
            session.close()
            exit(0)

        print(f'{session.username}\'s Cls on {session.version} not yet on {args.unmerged}:', file=sys.stderr)
        [print(cl) for cl in unmergedCls]
        session.close()
        exit(0)

    usernameFilter = (session.username if session.usernameSpecifiedThroughCmd else None)

    cls = P4Helper.getChangelists(
                                session.version,
                                developer=usernameFilter,
                                limit=args.limit,
                                fileRegex=args.file,
                                verbose=session.verbose)

    showFiles: bool = args.file is not None
    for cl in cls:
        print(cl.toString(withFiles=showFiles))

    session.close()
    exit(0)