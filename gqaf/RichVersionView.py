
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
ChangelistCallback = Callable[[Changelist], str]

class Row:
    def __init__(self):
        pass # attributes will be added dynamically
        # self.changelist = ...
        # self.developer = ...
        # self.cpp = ...

class RichVersionView:

    def __init__(self):

        self.columnNames: list[str] = []
        self.columnCallbacks: list[ChangelistCallback] = []
        self.errorsPerCl: dict[int, list[str]] = {}

    def addColumn(self, name: str, callback: ChangelistCallback):

        name = name.lower()
        self.columnNames.append(name)
        self.columnCallbacks.append(callback)

    def modifyColumn(self, name: str, newCallBack: ChangelistCallback):

        name = name.lower()

        columnIndex: int = -1
        for i, col in enumerate(self.columnNames):

            if col.lower() == name:
                columnIndex = i
                break

        assert i != -1, 'Tried to modify column which doesn\'t exist'
        self.columnCallbacks[i] = newCallBack

    def addSafetyNetStatus(self, jobsPool: dict[int, list[DeploymentJob]]):

        def getTotalTakenJobs(cl: Changelist) -> str:

            clJobs: list[DeploymentJob] = jobsPool.get(cl.value, [])

            failedJobs = [j for j in clJobs if j.isTaken()]
            return str(len(failedJobs))

        tpksPerCl: dict[tuple, list[DeploymentJob]] = {}
        for cl, pushedJobs in jobsPool.items():
            for job in pushedJobs:

                key: tuple = (cl, job.getTpkName())

                if key not in tpksPerCl:
                    tpksPerCl[key] = []

                tpksPerCl[key].append(job)

        def getTotalFailedJobs(cl: Changelist) -> str:

            clJobs: list[DeploymentJob] = jobsPool.get(cl.value, [])

            res: int = 0
            seenTpks: set[str] = set()
            for j in clJobs:

                if j.getTpkName() in seenTpks:
                    continue

                seenTpks.add(j.getTpkName())
                key: tuple = (cl.value, j.getTpkName())

                if any(tpk.isPassed() for tpk in tpksPerCl[key]):
                    continue

                if any(tpk.isFailed() for tpk in tpksPerCl[key]):
                    res += 1

            return str(res)

        def getTotalPassedJobs(cl: Changelist) -> str:

            clJobs: list[DeploymentJob] = jobsPool.get(cl.value, [])

            seenTpks: set[str] = set()
            res: int = 0
            for j in clJobs:

                if j.getTpkName() in seenTpks:
                    continue

                seenTpks.add(j.getTpkName())

                key: tuple = (cl.value, j.getTpkName())

                if any(tpk.isPassed() for tpk in tpksPerCl[key]):
                    res += 1

            return str(res)

        self.addColumn('tpks', getTotalTakenJobs)
        self.addColumn('red', getTotalFailedJobs)
        self.addColumn('passed', getTotalPassedJobs)

    def addPipeline(self, pipelineName:str, link: str):

        link = link.strip('/')
        pipeline = JenkinsRequestHandler.getPipelineInfo(link)
        pool = getPipelineBuildsByChangelist(pipeline)

        self.addColumn(pipelineName, getPipelineStatus(pool, self.errorsPerCl))

    def buildRows(self, changelists: list[Changelist]) -> list[Row]:

        self.errorsPerCl.clear()

        rows: list[Row] = []
        for cl in changelists:

            row = Row()

            for i, callback in enumerate(self.columnCallbacks):

                colName = self.columnNames[i]
                colValue: str = str(callback(cl))

                colValue = colValue.replace(',', ' ').replace('\n', ' ').replace('\t', ' ')
                setattr(row, colName, colValue)

            rows.append(row)

        return rows

    def buildCsv(self, changelists: list[Changelist]) -> str:

        rows = self.buildRows(changelists)
        csvContent: str = objectListToTableStr(rows, csv=True)
        return csvContent

    def buildAndPrint(self, changelists: list[Changelist], csv: bool = False):

        rows = self.buildRows(changelists)
        printObjectList(rows, csv=csv)

def createRichJenkinsView(cppPool: dict[int, JenkinsBuild], asanPool: dict[int, JenkinsBuild]) -> RichVersionView:

    jenkinsRichView = RichVersionView()
    jenkinsRichView.addColumn('developer', lambda cl: cl.developer)
    jenkinsRichView.addColumn('changelist', lambda cl: cl.value)

    jenkinsRichView.addColumn('cpp', getPipelineStatus(cppPool))

    jenkinsRichView.addColumn('cppReason', getPipelineFailureMessage(cppPool))

    jenkinsRichView.addColumn('asan', getPipelineStatus(asanPool))

    jenkinsRichView.addColumn('asanReason', getPipelineFailureMessage(asanPool))

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

def getPipelineFailureMessage(pool: dict[int, JenkinsBuild]) -> str:

    def f(cl: Changelist):

        if not pool or not (cl.value in pool):
            return '----'

        build = pool[cl.value]

        if not build.isFailed():
            return '----'

        _, message = build.guessFailureReason()
        return message

    return f

def getPipelineStatus(pool: dict[int, JenkinsBuild], errorsPerCl: dict[int, list[str]] = None) -> str:

    def f(cl: Changelist):

        if not pool or not (cl.value in pool):
            return '----'

        build = pool.get(cl.value)

        if not build.isFailed():
            return build.status()

        reason, errorMessage = build.guessFailureReason()

        if errorsPerCl is not None:
            errorsPerCl.setdefault(cl.value, []).append(reason.name + ': ' + errorMessage)

        return 'RED' if reason.name == 'Unknown' else reason.name

    return f

def getLinuxSetupsStatus(setupsPool: dict[int, list[BuildJob]]) -> callable:

    def f(cl: Changelist):

        builds = [build for build in setupsPool.get(cl.value, []) if build.isLinux()]

        if len(builds) == 0:
            return '----'

        bestBuild = max(builds, key=lambda b: b.relevancy())
        return bestBuild.status

    return f

def getWindowsSetupsStatus(setupsPool: dict[int, list[BuildJob]]) -> callable:

    def f(cl: Changelist):

        builds = [build for build in setupsPool.get(cl.value, []) if build.isWindows()]

        if len(builds) == 0:
            return '----'

        bestBuild = max(builds, key=lambda b: b.relevancy())
        return bestBuild.status

    return f

def createAlienTeamExampleVersionView(session: SessionInfo) -> RichVersionView:

    alienVersionView = RichVersionView()
    alienVersionView.addColumn('developer', lambda cl: cl.developer)
    alienVersionView.addColumn('changelist', lambda cl: cl.value)

    alienVersionView.addColumn('windows', getWindowsSetupsStatus(session.fetchSetupsPool()))
    alienVersionView.addColumn('linux', getLinuxSetupsStatus(session.fetchSetupsPool()))

    alienVersionView.addSafetyNetStatus(session.fetchJobsPool())

    cppLink = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{session.version}/job/CppValidation/'
    alienVersionView.addPipeline('cpp', cppLink)

    asanLink = f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{session.version}/job/AsanValidation/'
    alienVersionView.addPipeline('asan', asanLink)

    # FREYJA
    freyjaLink = f'https://cje-core.fr.murex.com/assets/job/FreyjaAlien/job/{session.version}/'
    alienVersionView.addPipeline('freyja', freyjaLink)

    alienVersionView.addColumn('defect', lambda cl: f'[{cl.defect}]')
    alienVersionView.addColumn('description', lambda cl: cl.description)
    return alienVersionView

if __name__ == '__main__':

    session = SessionInfo()

    parser = argparse.ArgumentParser('Show rich version view')

    parser.add_argument('--csv', action='store_true', default=False, help='Output in CSV format')
    parser.add_argument('--all', action='store_true', default=False, help='Show all changelists instead of 20')

    args, _ = parser.parse_known_args()

    changelists = session.fetchChangelistPool(lazy=True, limit=20)

    alienVersionView = createAlienTeamExampleVersionView(session)
    alienVersionView.buildAndPrint(changelists, args.csv)
    session.close()