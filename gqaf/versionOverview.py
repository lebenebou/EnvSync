
import argparse

from typing import List, Dict
from GqafRequestHandler import printObjectList, DeploymentJob
from JenkingsRequestHandler import JenkinsRequestHandler, getPipelineBuildsByChangelist, FailureReason
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
        self.freyja: str = None

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

    freyjaLink = f'https://cje-core.fr.murex.com/assets/job/FreyjaAlien/job/{session.version}/'
    freyjaPipeline = JenkinsRequestHandler.getPipelineInfo(freyjaLink)
    freyjaPool = getPipelineBuildsByChangelist(freyjaPipeline)

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

        clJobs: List[DeploymentJob] = jobsPool.get(cl.value, [])
        richRow.jobsPushed = len(clJobs)

        redJobs = len([j for j in clJobs if j.isFailed()])
        greenJobs = len([j for j in clJobs if j.isPassed()])

        richRow.cpp = '----'
        if cppPool and cl.value in cppPool:

            build = cppPool.get(cl.value)
            richRow.cpp = build.status()

            if build.isFailed():
                reason, _ = build.guessFailureReason()
                richRow.cpp = 'RED' if reason.name == 'Unknown' else reason.name

        richRow.asan = '----'
        if asanPool and cl.value in asanPool:

            build = asanPool.get(cl.value)
            richRow.asan = build.status()

            if build.isFailed():
                reason, _ = build.guessFailureReason()
                richRow.asan = 'RED' if reason.name == 'Unknown' else reason.name

        richRow.freyja = '----'
        if freyjaPool and cl.value in freyjaPool:
            richRow.freyja = freyjaPool.get(cl.value).status()

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