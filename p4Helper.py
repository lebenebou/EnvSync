
import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

import cli
import re

from concurrent.futures import ThreadPoolExecutor, as_completed

import xml.etree.ElementTree as xmlParser
from typing import List, Dict, Set, Callable

import argparse

class Changelist:
    p4Pattern = r'^Change\s+(\d+).*\s+by\s+(\S+)@'
    tagPattern = r"\[\s*(.*?)\s*]"

    def __init__(self, value: int = 0):

        self.value = int(value)
        self.defect = None
        self.description = None
        self.tags: List[str] = []
        self.developer = None

        self.fullInfoFetched: bool = False
        self.version: str = None
        self.files: List[str] = []

        self.gitCommit: str = None

    @staticmethod
    def fromP4CmdOutput(outputLines: List[str], startIndex: int = 0):

        # INPUT: p4 command output, and a start index
        # OUTPUT: tuple of (parsed Changelist , index of next changelist in the output)

        i: int = startIndex
        m = re.match(Changelist.p4Pattern, outputLines[i])
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
                    file, version = P4Helper.parsePathFromDepoPath(outputLines[i])
                    cl.version = version
                    cl.files.append(f'{version}/{file}')
                    i += 1

                return (cl, -1)

    def fetchFullInfo(self, verbose: bool = False):

        if self.developer == 'builder':
            print(f'Skipped fetching info for "builder" user: CL {self.value}', file=sys.stderr)
            return

        if self.fullInfoFetched:
            return

        command = f'p4 describe -s {self.value}'
        if verbose:
            print(f'Fetching affected files for changelist {self.value} (command: {command})', file=sys.stderr)

        result = cli.runCommand(command)
        if result.returncode != 0:
            print(f'{command} failed, could not retrieve info for this changelist', file=sys.stderr)
            return

        output: List[str] = result.stdout.splitlines()
        tmpCL, _ = Changelist.fromP4CmdOutput(output)

        self.files = list(tmpCL.files)
        self.version = tmpCL.version

        self.fullInfoFetched = True
        return

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
            self.fetchFullInfo()
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

        # Parse defect
        defectPattern: str = rf'\[({P4Helper.DefectRegex})\]' 
        m = re.search(defectPattern, self.description)
        if m:
            self.defect = m.group(1)
            self.description = re.sub(defectPattern, '', self.description)

        # parse [tags]
        for m in re.finditer(Changelist.tagPattern, self.description):

            matchstr = m.group(1).strip()
            self.tags.append(re.sub('\s+', '', matchstr))

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
 
        self.description = self.description.replace('&', '&amp;')
        self.description = self.description.split('</mxp4Root>')[0] + '</mxp4Root>'

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
    def parsePathFromDepoPath(depoPath: str) -> tuple[str, str]:

        depoPath = depoPath.strip(' ').strip('.').strip(' ')
        pattern = r'depot/(v[^/]+)/(.*)#'
        m = re.search(pattern, depoPath)

        if not m:
            return None

        file = m.group(2)
        version = m.group(1)
        return file, version

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
        cl.fullInfoFetched = True
        return cl

    @staticmethod
    def extractMergedDefects(inputDefects: Set[str], destVersion: str, destDevs: Set[str], verbose: bool = None) -> Dict[str, Changelist]:

        # OUTPUT
        # The defects out of <inputDefects> which were merged on <destVersion> by ANY of the <destDevs>

        inputDefects = set(defect for defect in inputDefects if defect)
        invalidDefect: str = next((d for d in inputDefects if not re.match('DEF\d+', d)), None)
        assert not invalidDefect, f'Not a defect ID: {invalidDefect}'

        destDevs: Set[str] = set(destDevs)
        destDevs.discard('builder')

        fetchDevDestCls: Callable[[str], List[Changelist]] = lambda dev: list(P4Helper.getChangelists(destVersion, developer=dev, verbose=verbose))

        mergedDefects: Dict[str, Changelist] = {}
        with ThreadPoolExecutor() as executor:

            destClFutureByDev = {executor.submit(fetchDevDestCls, dev) : dev for dev in destDevs}

            for clFuture in as_completed(destClFutureByDev):

                devWhoMerged: str = destClFutureByDev[clFuture]
                hisMergedCls: List[Changelist] = clFuture.result()

                for mergedCl in hisMergedCls:
                    if mergedCl.defect in inputDefects:
                        mergedDefects[mergedCl.defect] = mergedCl

        return mergedDefects

    from typing import Generator
    @staticmethod
    def getChangelists(version: str, *, developer: str = None, limit: int = None, fileRegex: str = None, verbose: bool = False) -> Generator[Changelist, None, None]:

        if version == P4Helper.Build and not limit and not developer: # getting all changelists on build takes a lot of time
            limit = 1000

        command = 'p4 changes -l -s submitted'

        if developer:
            command += f' -u {developer}'

        if limit:
            command += f' -m {limit}'

        command += f' {P4Helper.depoVersion(version)}'

        if verbose is not None:
            logMessage: str = 'Getting'

            if developer:
                logMessage += f' {developer}'

            logMessage += f' changelists on {version}...'

            if limit:
                logMessage += f' (Limiting to {limit} changelists)'

            print(logMessage, file=sys.stderr, flush=True)

        if verbose:
            print(f'Running command: {command}', file=sys.stderr)

        result = cli.runCommand(command)

        if result.returncode != 0:
            print(f'Failed to get changelists on {version}', file=sys.stderr)
            return []

        changelists: List[Changelist] = []
        outputLines: List[str] = result.stdout.splitlines()

        if len(outputLines) == 0:
            return []

        # Parse the output for changelists and descriptions
        nextClIndex = 0
        while nextClIndex != -1:

            cl, nextClIndex = Changelist.fromP4CmdOutput(outputLines, nextClIndex)
            cl.parseAndCleanDescription()
            changelists.append(cl)

        # at this point we have the chaneglists and their parsed descriptions

        for cl in changelists:

            if fileRegex:
                cl.fetchFullInfo(verbose)

            noFilesMatchRegex: bool = fileRegex and not any(re.search(fileRegex, f, re.IGNORECASE) for f in cl.files)
            if noFilesMatchRegex:
                continue

            if False: # extensible for more filters in the future
                continue

            yield cl

    @staticmethod
    def getUnmergredChangelists(src: str, dest: str, dev: str = None, verbose: bool = False) -> List[Changelist]:

        srcCls = P4Helper.getChangelists(version=src, developer=dev, verbose=verbose)
        destCls = P4Helper.getChangelists(version=dest, developer=dev, verbose=verbose)

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