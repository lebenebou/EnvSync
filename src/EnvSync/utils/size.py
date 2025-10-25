
import os
import sys
import argparse

def getFileSizeMb(filePath: str) -> float:

    sizeB = os.path.getsize(filePath)
    return sizeB / (1024 * 1024)

def printSize(filePath: str) -> int: # returnCode

    if not os.path.exists(filePath):
        print(f"File doesn't exist: {filePath}", file=sys.stderr)
        return 1

    if not os.path.isfile(filePath):
        print(f"Not a file: {filePath}", file=sys.stderr)
        return 1

    fileSize = getFileSizeMb(filePath)
    print(f"{filePath}: {round(fileSize, 3)} MB", file=sys.stdout)
    return 0

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Check size of a file')
    parser.add_argument('file_paths', nargs='+', help='File paths')

    args = parser.parse_args()
    filePaths = args.file_paths

    if len(filePaths) == 0:
        parser.print_help()
        exit(1)

    returnCodes = [printSize(f) for f in filePaths]
    exit(all(returnCodes))