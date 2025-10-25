
import os
import argparse
from EnvSync.utils.start import startItemOrProcess

CURRENT_DIR = os.getcwd()

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs='?', default=CURRENT_DIR, help="path of the folder to open")

    args = parser.parse_args()

    itemPath = args.path

    if itemPath == ".":
        itemPath = CURRENT_DIR

    if os.path.isdir(itemPath):
        startItemOrProcess(itemPath)
        exit(0)

    itemPath = os.path.dirname(itemPath)
    if itemPath == "":
        itemPath = CURRENT_DIR

    startItemOrProcess(itemPath)