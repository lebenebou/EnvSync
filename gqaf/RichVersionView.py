
import argparse

from typing import List, Callable
from GqafRequestHandler import printObjectList, DeploymentJob, BuildJob, objectListToTableStr
from JenkinsRequestHandler import JenkinsRequestHandler, getPipelineBuildsByChangelist, JenkinsBuild
from SessionInfo import SessionInfo

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

import sys
sys.path.append(PARENT_DIR)

from p4Helper import Changelist
CellValueCallback = Callable[[Changelist], str]

class Row:
    def __init__(self):
        pass # attributes will be added dynamically
        # self.changelist = ...
        # self.developer = ...
        # self.cpp = ...

class RichVersionView:

    def __init__(self):

        self.columnNames: list[str] = []
        self.columnCallbacks: list[CellValueCallback] = []

    def addColumn(self, name: str, callback: CellValueCallback):
        self.columnNames.append(name)
        self.columnCallbacks.append(callback)

    def buildRows(self, changelists: list[Changelist]) -> list[Row]:

        rows: list[Row] = []
        for cl in changelists:

            row = Row()

            for i, callback in enumerate(self.columnCallbacks):
                colName = self.columnNames[i]
                setattr(row, colName, callback(cl))

            rows.append(row)

        return rows

    def toCsv(self, changelists: list[Changelist]) -> str:

        rows = self.buildRows(changelists)
        csvContent: str = objectListToTableStr(rows, csv=True)
        return csvContent

    def printOut(self, changelists: list[Changelist], csv: bool = False):

        rows = self.buildRows(changelists)
        printObjectList(rows, csv=csv)

def createRichJenkinsView(cppPool: dict[int, JenkinsBuild], asanPool: dict[int, JenkinsBuild]) -> RichVersionView:

    jenkinsRichView = RichVersionView()
    jenkinsRichView.addColumn('developer', lambda cl: cl.developer)
    jenkinsRichView.addColumn('changelist', lambda cl: cl.value)

    def getCppStatus(cl: Changelist) -> str: return getPipelineStatus(cppPool, cl)
    jenkinsRichView.addColumn('cpp', getCppStatus)

    def getCppFailureMessage(cl: Changelist) -> str: return getPipelineFailureMessage(cppPool, cl)
    jenkinsRichView.addColumn('cppReason', getCppFailureMessage)

    def getAsanStatus(cl: Changelist) -> str: return getPipelineStatus(asanPool, cl)
    jenkinsRichView.addColumn('asan', getAsanStatus)

    def getAsanFailureMessage(cl: Changelist) -> str: return getPipelineFailureMessage(asanPool, cl)
    jenkinsRichView.addColumn('asanReason', getAsanFailureMessage)

    jenkinsRichView.addColumn('description', lambda cl: cl.allTags(True))

    return jenkinsRichView

def createSetupsView(setupsPool: dict[int, list[BuildJob]]) -> RichVersionView:

    setupsRichView = RichVersionView()
    setupsRichView.addColumn('developer', lambda cl: cl.developer)
    setupsRichView.addColumn('changelist', lambda cl: cl.value)

    def getWindowsSetupsStatus(cl: Changelist) -> str:

        builds = [build for build in setupsPool.get(cl.value, []) if build.isWindows()]
        if len(builds) == 0:
            return '----'
        else:
            bestBuild = max(builds, key=lambda b: b.relevancy())
            return bestBuild.status
    setupsRichView.addColumn('windows', getWindowsSetupsStatus)

    def getLinuxSetupsStatus(cl: Changelist) -> str:

        builds = [build for build in setupsPool.get(cl.value, []) if build.isLinux()]
        if len(builds) == 0:
            return '----'
        else:
            bestBuild = max(builds, key=lambda b: b.relevancy())
            return bestBuild.status
    setupsRichView.addColumn('linux', getLinuxSetupsStatus)

    def getLinuxSetupsBuildId(cl: Changelist) -> str:

        bestLinuxBuild: BuildJob = None
        bestWindowsBuild: BuildJob = None

        linuxBuilds: list[BuildJob] = setupsPool.get(cl.value, None)

        if not linuxBuilds:
            return '----'

        bestLinuxBuild = max(linuxBuilds, key=lambda b: b.relevancy())
        return bestLinuxBuild.buildId

    setupsRichView.addColumn('buildId', getLinuxSetupsBuildId)

    setupsRichView.addColumn('description', lambda cl: f'[{cl.defect}]{cl.allTags()}{cl.description[:30]}')

    return setupsRichView

def getPipelineFailureMessage(pool: dict[int, JenkinsBuild], cl: Changelist) -> str:

    if not pool or not (cl.value in pool):
        return '----'

    build = pool[cl.value]

    if not build.isFailed():
        return '----'

    _, message = build.guessFailureReason()
    return message

def getPipelineStatus(pool: dict[int, JenkinsBuild], cl: Changelist) -> str:

    if not pool or not (cl.value in pool):
        return '----'

    build = pool.get(cl.value)

    if build.isFailed():
        reason, _ = build.guessFailureReason()
        return 'RED' if reason.name == 'Unknown' else reason.name

    return build.status()

if __name__ == '__main__':

    session = SessionInfo()

    parser = argparse.ArgumentParser('Show rich version view')

    parser.add_argument('--csv', action='store_true', default=False, help='Output in CSV format')
    parser.add_argument('--all', action='store_true', default=False, help='Show all changelists instead of 20')

    args, _ = parser.parse_known_args()

    myView = RichVersionView(session.fetchChangelistPool(True, 20))
    myView.addColumn('developer', lambda cl: cl.developer)
    myView.addColumn('changelist', lambda cl: cl.value)

    def getLinuxSetupsStatus(cl: Changelist) -> str:

        setupsPool = session.fetchSetupsPool(lazy=True)
        builds = [build for build in setupsPool.get(cl.value, []) if build.isLinux()]
        if len(builds) == 0:
            return '----'
        else:
            bestBuild = max(builds, key=lambda b: b.relevancy())
            return bestBuild.status
    myView.addColumn('linux', getLinuxSetupsStatus)

    def getNumberOfJobsPushed(cl: Changelist) -> str:

        jobsPool = session.fetchJobsPool(True)
        clJobs: List[DeploymentJob] = jobsPool.get(cl.value, [])

        redJobs = len([j for j in clJobs if j.isFailed()])
        greenJobs = len([j for j in clJobs if j.isPassed()])

        return str(len(clJobs))
    myView.addColumn('jobspushed', getNumberOfJobsPushed)

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

    def getCppPipelineStatus(cl: Changelist) -> str:
        return getPipelineStatus(cppPool, cl)
    myView.addColumn('cpp', getCppPipelineStatus)

    def getAsanPipelineStatus(cl: Changelist) -> str:
        return getPipelineStatus(asanPool, cl)
    myView.addColumn('asan', getAsanPipelineStatus)

    def getFreyjaPipelineStatus(cl: Changelist) -> str:
        return getPipelineStatus(freyjaPool, cl)
    myView.addColumn('freyja', getFreyjaPipelineStatus)

    myView.addColumn('info', lambda cl: f'[{cl.defect}]' + cl.allTags())

    myView.printOut(args.csv)
    session.close()