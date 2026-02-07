
import sys, os
import argparse

import pyperclip

CURRENT_DIR = os.getcwd()

def openFolderInExplorer(folderPath: str):

    folderPath = os.path.abspath(folderPath)
    os.startfile(folderPath)

def openFileInDefaultApp(filePath: str):

    filePath = os.path.abspath(filePath)
    os.startfile(filePath)

def openCmdInFolder(folderPath: str):

    folderPath = os.path.abspath(folderPath)
    os.system(f"start cmd /K cd /D {folderPath}")
    
def startItemOrProcess(itemPath: str = None):

    if itemPath is None:
        return startItemOrProcess(pyperclip.paste().strip())
        exit(0)

    if itemPath == ".":
        itemPath = CURRENT_DIR

    if itemPath.startswith('http'):
        os.startfile(itemPath)
        exit(0)

    if not os.path.exists(itemPath):
        print(f"Path does not exist: {itemPath}", file=sys.stderr, flush=True)
        sys.exit(1)

    if os.path.isdir(itemPath):
        openFolderInExplorer(itemPath)
        exit(0)

    if os.path.isfile(itemPath):
        openFileInDefaultApp(itemPath)
        exit(0)

    print(f"Path is not a file or folder: {itemPath}", file=sys.stderr, flush=True)
    sys.exit(1)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs='?', default=None, help="path of the item to start")

    args = parser.parse_args()

    startItemOrProcess(args.path)