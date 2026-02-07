
import sys, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from src.GlobalEnv import GlobalEnv, ConfigScope

def printCurrentScope():

    print('[INFO] Current config scope includes:')

    for scope in ConfigScope:
        if scope & GlobalEnv().currentScope:
            print(f'\t- {scope.name}')

if __name__ == '__main__':

    globalEnv = GlobalEnv()

    printCurrentScope()
    exit(0)