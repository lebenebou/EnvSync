
from EnvSync.utils.cli import commandOutput

HOSTNAME = commandOutput('hostname').strip()
PERSONAL_PC_NAME = 'LebenebouPC'
HOME_PC_NAME = 'LebenebouPC'

from enum import IntFlag
class ConfigScope(IntFlag):

    MUREX = 1
    LAPTOP = 2
    HOME_PC = 4

    NVIM = 8
    OBSIDIAN = 16

    COMMON = MUREX | LAPTOP | HOME_PC

class ConfigOption:

    def __init__(self):

        self.tag = None
        self.comment = None
        self.scope = ConfigScope.COMMON

    def withTag(self, tag: str):

        if not tag:
            self.tag = None
            return self

        self.tag = tag.strip().capitalize()
        return self

    def withScope(self, newScope):

        if self.scope == ConfigScope.COMMON:
            self.scope = 0

        self.scope |= newScope
        return self

    def withComment(self, comment: str):

        self.comment = comment
        return self

    def toString(self) -> str:
        raise NotImplementedError("This method is virtual, please override")

CURRENT_SCOPE = ConfigScope.LAPTOP

if HOSTNAME.lower() == 'dell163rws'.lower():
    CURRENT_SCOPE = ConfigScope.MUREX

if HOSTNAME.lower() == 'home-pc'.lower():
    CURRENT_SCOPE = ConfigScope.HOME_PC

class ConfigFile:

    def __init__(self):
        self.options: list[ConfigOption] = []

    def add(self, option: ConfigOption):
        self.options.append(option)

    def commentChar(self) -> chr:
        raise NotImplementedError("This method is virtual, please override")

    def createTagOrComment(self, optionTagOrComment: str = None) -> str:

        if not optionTagOrComment:
            return ""

        return f'{self.commentChar()} {optionTagOrComment}\n'

    def toString(self, scopeFilter = CURRENT_SCOPE):
        
        res = '\n'
        currentTag = None
        for option in (op for op in self.options if op.scope & scopeFilter):
            
            if currentTag != option.tag:

                res += "\n"
                res += self.createTagOrComment(option.tag)

                currentTag = option.tag

            res += option.toString()

            if option.comment:
                res += ' ' + self.createTagOrComment(option.comment)

            if not res.endswith("\n"):
                res += "\n"

        return res

    @staticmethod
    def writeToFile(path: str, stringStream: str):
        open(path, 'w').write(stringStream)


def runUnitTests():
    
    assert (ConfigScope.MUREX | ConfigScope.LAPTOP) == 3

def printCurrentScope():
    
    print('Current config scope includes:')

    for scope in ConfigScope:
        if scope & CURRENT_SCOPE:
            print(f'- {scope.name}')

if __name__ == '__main__':

    runUnitTests()
    printCurrentScope()