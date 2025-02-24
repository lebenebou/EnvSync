
import sys
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

import cli
import re

import xml.etree.ElementTree as xmlParser
from typing import List

import argparse

def parsePathFromDepoPath(depoPath: str) -> str:

    pattern = r'depot/v3\.1\.\S+?/(.*)#'
    m = re.search(pattern, depoPath)

    if not m:
        return None

    file = m.group(1)
    return file

class Changelist:
    pattern = r'^Change\s+(\d+).*\s+by\s+(\S+)@'
    tagPattern = r"\[(.*?)\]"

    def __init__(self, value: int = 0):

        self.value = int(value)
        self.defect = None
        self.description = None
        self.tags: List[str] = []
        self.developer = None

        self.files: List[str] = []

        self.gitCommit: str = None

    def fetchAffectedFiles(self, verbose: bool = False):

        if self.files:
            return

        command = f'p4 describe {self.value}'
        if verbose:
            print(f'Fetching affected files for changelist {self.value} (command: {command})', file=sys.stderr)

        result = cli.runCommand(command)
        if result.returncode != 0:
            print(f'p4 describe {self.value} failed, could not retrieve files for this changelist', file=sys.stderr)
            return

        output: List[str] = result.stdout.splitlines()
        i: int = 0
        while True:
            i+=1
            if output[i].lower().count('affected files'):
                break
        i+=2

        self.files: List[str] = []
        while True:

            file = output[i].strip(' ').strip('.').strip(' ')
            self.files.append(file)

            i+=1
            if output[i].strip(' ') == '':
                break

        self.files = [parsePathFromDepoPath(f) for f in self.files]
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

        if not withFiles:
            return s

        self.fetchAffectedFiles()
        s += '\n\t'
        s += '\n\t'.join(self.files)
        s += '\n'

        return s

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
        
    def parseDescription(self, verbose: bool = False):

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

            if matchstr.startswith('DEF'):
                self.defect = matchstr
            else:
                self.tags.append(matchstr)

        # remove [tags]
        self.description = re.sub(Changelist.tagPattern, '', self.description).strip()

        # remove (cherry picked from commit X)...
        cherryPickPattern: str = r'\(cherry\s+picked\s+from\s+commit\s+(\S+)\).*'
        m = re.search(cherryPickPattern, self.description)
        if m:
            self.gitCommit = m.group(1)
            self.description = re.sub(cherryPickPattern, '', self.description).strip()

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
    def getChangelists(version: str, developer: str = None, limit: int = None, specificChangelist: int = None, verbose: bool = False) -> Generator[Changelist, None, None]:

        print(f'Getting changelists on {version}...', end='', file=sys.stderr)

        command = 'p4 changes -l -s submitted'

        if version == P4Helper.Build and not limit and not developer and not specificChangelist: # getting all changelists on build takes a lot of time
            limit = 500

        if limit:
            print(f' (Limiting search to {limit} changelists)', end='', file=sys.stderr)
            command += f' -m {limit}'

        print(end='\n', file=sys.stderr, flush=True)

        if developer:
            command += f' -u {developer}'

        command += f' {P4Helper.depoVersion(version)}'

        if specificChangelist:
            command += f'@{specificChangelist},{specificChangelist}' # @123,123 (this filters on an inclusive range, it's a hack to filter on a specific changelist)

        if verbose:
            print(f'Running command: {command}', file=sys.stderr)

        result = cli.runCommand(command)

        if result.returncode != 0:
            print(f'Failed to get changelists on {version}', file=sys.stderr)
            return []

        output: List[str] = result.stdout.splitlines()

        i: int = 0
        while i < len(output):

            line = output[i]
            m = re.search(Changelist.pattern, line)

            cl = Changelist()
            cl.value, cl.developer = m.groups()
            cl.description = ''

            i += 2
            while i < len(output) and not output[i].startswith('Change'):
                cl.description += output[i] 
                i+=1

            cl.parseDescription(verbose)
            yield cl

    @staticmethod
    def getUnmergredChangelists(src: str, dest: str, developer: str = None, verbose: bool = False) -> List[Changelist]:

        # returns changelists submitted by <developer> that are NOT merged from src to dest, based on defectID

        srcCls = P4Helper.getChangelists(src, developer, limit=None, verbose=verbose)

        destCls = P4Helper.getChangelists(dest, developer, limit=None, verbose=verbose)

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
    parser.add_argument('-l', '--limit', default=None, type=int, help='limit the output to a certain number of changelists')
    parser.add_argument('-f', '--file', type=str, nargs='?', const='*', default=None, help='output changelit files. if value is given, filter on matching files by substring')

    args, _ = parser.parse_known_args()

    if args.unmerged is not None:

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

    for cl in P4Helper.getChangelists(session.version, usernameFilter, args.limit, session.changelist, session.verbose):

        if not args.file:
            print(cl)
            continue

        cl.fetchAffectedFiles(session.verbose)

        if args.file == '*':
            print(cl.toString(withFiles=True))
            continue

        if any(file.lower().count(args.file.lower()) for file in cl.files):
            print(cl.toString(withFiles=True))

        cl.fetchAffectedFiles(session.verbose)

        if args.file is True:
            print(cl.toString(withFiles=True))
            continue

        if any(file.lower().count(args.file.lower()) for file in cl.files):
            print(cl.toString(withFiles=True))

    session.close()
    exit(0)