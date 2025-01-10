
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
from p4Helper import P4Helper

def get100ChangelistsOnBuild():
    list(P4Helper.getChangelists(P4Helper.Build, developer=None, limit=100))

def getUsersChangelistsOnBuild():
    list(P4Helper.getChangelists(P4Helper.Build, developer=settings.getUsername(), limit=100))

def getChangelistsOnCurrentVersion():
    list(P4Helper.getChangelists(VERSION))

def getUserChangelistsOnCurrentVersion():
    list(P4Helper.getChangelists(VERSION, developer=settings.getUsername()))

# GQAF API
from gqaf.GqafRequestHandler import GqafRequestHandler

def fetchSetups():
    GqafRequestHandler.fetchBuildJobs(VERSION)

def fetchJobs():
    GqafRequestHandler.fetchDeploymentJobs(VERSION)

if __name__ == '__main__':

    print('P4Helper' + 20*'-')
    benchmarkFunction(get100ChangelistsOnBuild)
    print()
    benchmarkFunction(getUserChangelistsOnCurrentVersion)
    benchmarkFunction(getChangelistsOnCurrentVersion)
    print()
    print('GQAF API' + 20*'-')
    benchmarkFunction(GqafRequestHandler.getAllMxVersions)
    benchmarkFunction(fetchSetups)
    benchmarkFunction(fetchJobs)
    print()