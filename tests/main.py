
from GlobalEnv import GlobalEnv, ConfigScope

def printCurrentScope():

    print('[INFO] Current config scope includes:')

    for scope in ConfigScope:
        if scope & GlobalEnv().currentScope:
            print(f'\t- {scope.name}')

if __name__ == '__main__':

    globalEnv = GlobalEnv()

    printCurrentScope()
    exit(0)