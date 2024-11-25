
from GqafRequestHandler import GqafRequestHandler, DeploymentJob, BuildJob
from p4Helper import Changelist, P4Helper
from SessionInfo import SessionInfo

import sys

def getChangelistsBetween(start: int, end: int, allChangelists: list[Changelist]) -> list[Changelist]:

    if start < end:
        start, end = end, start

    return [cl for cl in allChangelists if cl.value <= start and cl.value >= end]

class TPK:
    def __init__(self, job: DeploymentJob):
        self.testPackage = job.testPackage
        self.nickname = job.nickname
        self.jobsDeployed: list[DeploymentJob]
        self.isPossiblyRandom = False

    def __str__(self) -> str:
        return f'{self.testPackage} - {self.nickname}'

    def __hash__(self):
        return hash((self.testPackage, self.nickname))

    def __eq__(self, other):
        
        if not isinstance(other, TPK):
            return False

        return self.testPackage == other.testPackage and self.nickname == other.nickname

    def fillJobsDeployed(self, jobs: list[DeploymentJob]):

        jobs = [j for j in jobs if j.testPackage == self.testPackage and j.nickname == self.nickname]
        self.jobsDeployed = sorted(jobs, key=lambda j: j.changelist, reverse=True)

    def latestChangelistPushedAt(self) -> int:

        if len(self.jobsDeployed) == 0:
            return None

        return self.jobsDeployed[0].changelist

    def isGreenAtLatestPush(self) -> bool:

        latestJobsPushed = [job for job in self.jobsDeployed if job.changelist == self.latestChangelistPushedAt()]
        return all(job.isPassed() for job in latestJobsPushed)

    def isRedAtLatestPush(self) -> bool:

        latestJobsPushed = [job for job in self.jobsDeployed if job.changelist == self.latestChangelistPushedAt()]
        return all(job.isFailed() for job in latestJobsPushed)

    def firstRedChangelist(self, lastGreenCl: int = None) -> int:

        if lastGreenCl is None:
            lastGreenCl = self.lastGreenChangelist()

        if lastGreenCl is None:
            return self.jobsDeployed[-1].changelist

        for job in reversed(self.jobsDeployed):

            if job.changelist <= lastGreenCl:
                continue

            if job.isFailed():
                return job.changelist

        return None

    def lastGreenChangelist(self) -> int:

        for job in self.jobsDeployed:

            if job.isPassed():
                return job.changelist

            continue

        return None

    def printStatus(self, version: str, setupsPool: dict[int, list[BuildJob]] = None):

        guiltyCls: list[Changelist] = self.getGuiltyChangelists(version)

        if len(guiltyCls) == 0:
            return

        print('-'*100, end='\n\n')
        print(f'{self}:')
        for cl in guiltyCls:
            print(cl)

        print(end='\n')

    def getGuiltyChangelists(self, version: str) -> list[Changelist]:

        if len(self.jobsDeployed) == 0:
            return []

        if self.isGreenAtLatestPush():
            return []

        if not self.isRedAtLatestPush():
            self.isPossiblyRandom = True
            return []

        lastGreenCl: int = self.lastGreenChangelist()
        firstRedCl: int = self.firstRedChangelist()
        allCls = P4Helper.getChangelists(version, detail=2)

        if lastGreenCl is None:
            return []

        guiltyCls = getChangelistsBetween(firstRedCl, lastGreenCl, allCls)
        guiltyCls.remove(Changelist(lastGreenCl))
        return guiltyCls

def getAllDeploymentJobs(version: str) -> list[DeploymentJob]:

    allDeploymentJobs: list[DeploymentJob] = GqafRequestHandler.fetchDeploymentJobs(version)
    allDeploymentJobs = [job for job in allDeploymentJobs if job.isFailed() or job.isPassed()]

    return allDeploymentJobs

def extractTpks(jobs: list[DeploymentJob]) -> set[TPK]:

    tpkSet = set()
    for job in jobs:

        tpk = TPK(job)
        if tpk in tpkSet: # based on TPK number and nickname
            continue

        tpk.fillJobsDeployed(jobs)
        tpkSet.add(tpk)

    return tpkSet

if __name__ == '__main__':

    session = SessionInfo()
    if not session.version:
        print('No version specified', file=sys.stderr)
        exit(1)

    allDeploymentJobs = getAllDeploymentJobs(session.version)
    tpks = extractTpks(allDeploymentJobs)

    for tpk in tpks:
        tpk.printStatus(session.version)

    exit(0)