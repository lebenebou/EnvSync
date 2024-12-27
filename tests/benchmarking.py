
import sys
import time

import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)

sys.path.append(PARENT_DIR)

import settings

def benchmarkFunction(f: callable):

    print(f'{f.__name__} will take...', end='\r', flush=True)

    startTime = time.perf_counter()
    f()
    endTime = time.perf_counter()

    elapsed = (endTime - startTime)*1000

    print(f'{f.__name__} took {int(elapsed)} ms', flush=True)

VERSION = settings.getCurrentVersion()

# P4Helper
from p4Helper import P4Helper, ChangelistDetail

def get100ChangelistsOnBuild():
    list(P4Helper.getChangelists(P4Helper.Build, developer=None, detail=ChangelistDetail.Minimal, limit=100))

def get100ChangelistsOnBuildWithDefects():
    list(P4Helper.getChangelists(P4Helper.Build, developer=None, detail=ChangelistDetail.Defect, limit=100))

def get100ChangelistsOnBuildWithDetails():
    list(P4Helper.getChangelists(P4Helper.Build, developer=None, detail=ChangelistDetail.Full, limit=100))

def getUsersChangelistsOnBuild():
    list(P4Helper.getChangelists(P4Helper.Build, developer=settings.getUsername(), detail=ChangelistDetail.Full, limit=100))

def getChangelistsOnCurrentVersion():
    list(P4Helper.getChangelists(VERSION))

def getUserChangelistsOnCurrentVersion():
    list(P4Helper.getChangelists(VERSION, developer=settings.getUsername()))

def getChangelistsOnCurrentVersionWithDefects():
    list(P4Helper.getChangelists(VERSION, detail=ChangelistDetail.Defect))

def getChangelistsOnCurrentVersionWithDetails():
    list(P4Helper.getChangelists(VERSION, detail=ChangelistDetail.Full))

# GQAF API
from gqaf.GqafRequestHandler import GqafRequestHandler

def fetchSetups():
    GqafRequestHandler.fetchBuildJobs(VERSION)

def fetchJobs():
    GqafRequestHandler.fetchDeploymentJobs(VERSION)

if __name__ == '__main__':

    print('P4Helper' + 20*'-')
    benchmarkFunction(get100ChangelistsOnBuild)
    benchmarkFunction(get100ChangelistsOnBuildWithDefects)
    benchmarkFunction(get100ChangelistsOnBuildWithDetails)
    print()
    benchmarkFunction(getUserChangelistsOnCurrentVersion)
    benchmarkFunction(getChangelistsOnCurrentVersion)
    benchmarkFunction(getChangelistsOnCurrentVersionWithDefects)
    benchmarkFunction(getChangelistsOnCurrentVersionWithDetails)
    print()
    print('GQAF API' + 20*'-')
    benchmarkFunction(GqafRequestHandler.getAllMxVersions)
    benchmarkFunction(fetchSetups)
    benchmarkFunction(fetchJobs)
    print()