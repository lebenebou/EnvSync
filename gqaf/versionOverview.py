
import argparse

from typing import List, Dict
from GqafRequestHandler import printObjectList
from JenkingsRequestHandler import JenkinsRequestHandler, getPipelineBuildsByChangelist
from SessionInfo import SessionInfo

class RichChangelistRow:

    def __init__(self):
        
        self.developer: str = None
        self.changelist: int = None

        self.linux: str = None
        self.jobsPushed: int = None

        self.cpp: str = None
        self.asan: str = None

        self.cpp: str = None
        self.asan: str = None

        self.info: str = None

def getRichRows(session: SessionInfo, limit: int = None) -> List[RichChangelistRow]:

    toReturn: List[RichChangelistRow] = []

    chaneglistPool = session.fetchChangelistPool(lazy=True, limit=limit)
    jobsPool = session.fetchJobsPool(lazy=True)
    setupsPool = session.fetchSetupsPool(lazy=True)

    # pipelines
    cppLink = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{session.version}/job/CppValidation/'
    cppPipeline = JenkinsRequestHandler.getPipelineInfo(cppLink)
    cppPool = getPipelineBuildsByChangelist(cppPipeline)

    asanLink = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{session.version}/job/AsanValidation/'
    asanPipeline = JenkinsRequestHandler.getPipelineInfo(asanLink)
    asanPool = getPipelineBuildsByChangelist(asanPipeline)

    for i, cl in enumerate(chaneglistPool):

        if limit and limit == i:
            break

        richRow = RichChangelistRow()
        richRow.changelist = cl.value
        richRow.developer = cl.developer

        linuxBuilds = [build for build in setupsPool.get(cl.value, []) if build.isLinux()]
        if len(linuxBuilds) == 0:
            richRow.linux = '----'
        else:
            bestLinuxBuild = max(linuxBuilds, key=lambda b: b.relevancy())
            richRow.linux = bestLinuxBuild.status

        richRow.jobsPushed = len(jobsPool.get(cl.value, []))

        richRow.cpp = '----'
        if cppPool and cl.value in cppPool:
            richRow.cpp = cppPool.get(cl.value).status()

        richRow.asan = '----'
        if asanPool and cl.value in asanPool:
            richRow.asan = asanPool.get(cl.value).status()

        richRow.info = cl.allTags(withDefect=True)

        toReturn.append(richRow)

    return toReturn

if __name__ == '__main__':

    session = SessionInfo()

    parser = argparse.ArgumentParser('Fetch setups')

    parser.add_argument('--csv', action='store_true', default=False, help='Output in CSV format')
    parser.add_argument('--all', action='store_true', default=False, help='Show all changelists')

    args, _ = parser.parse_known_args()

    richRows: List[RichChangelistRow] = getRichRows(session, (20 if not args.all else None))
    printObjectList(richRows, args.csv)
    session.close()