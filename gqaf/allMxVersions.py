
from GqafRequestHandler import GqafRequestHandler
from typing import List

if __name__ == '__main__':

    allMxVersions: List[str] = GqafRequestHandler.getAllMxVersions()
    
    for version in allMxVersions:
        print(version)