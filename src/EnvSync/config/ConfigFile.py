
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
REPO_ROOT = os.path.dirname(os.path.dirname(PARENT_DIR))
BIN_DIR = os.path.join(PARENT_DIR, 'Bin')

sys.path.append(PARENT_DIR)

HOME_DIR = os.path.expanduser('~')
TMP_FOLDER_PATH = os.path.join(HOME_DIR, 'config.tmp')
VIM_RC = os.path.join(HOME_DIR, '.vimrc')
NVIM_RC = os.path.join(HOME_DIR, 'AppData', 'Local', 'nvim', 'init.vim')
BASHPROFILE = os.path.join(HOME_DIR, '.bash_profile')

G_PAVILION_15 = os.path.join('G:\\', 'Other computers', 'Pavilion15')

from EnvSync.utils.cli import commandOutput

HOSTNAME = commandOutput('hostname').strip()
PERSONAL_PC_NAME = 'LebenebouPC'
HOME_PC_NAME = 'LebenebouPC'

class ConfigOption:

    # Scopes
    MUREX = 1
    LAPTOP = 2
    HOME_PC = 4

    NVIM = 8
    OBSIDIAN = 16

    COMMON = MUREX | LAPTOP | HOME_PC

    def __init__(self):

        self.tag = None
        self.comment = None
        self.scope = ConfigOption.COMMON

    def withTag(self, tag: str):

        if not tag:
            self.tag = None
            return self

        self.tag = tag.strip().capitalize()
        return self

    def withScope(self, newScope):

        if self.scope == ConfigOption.COMMON:
            self.scope = 0

        self.scope |= newScope
        return self

    def withComment(self, comment: str):

        self.comment = comment
        return self

    def toString(self) -> str:
        raise NotImplementedError("This method is virtual, please override")

CURRENT_SCOPE = ConfigOption.LAPTOP

if HOSTNAME.lower() == 'dell163rws'.lower():
    CURRENT_SCOPE = ConfigOption.MUREX

if HOSTNAME.lower() == 'home-pc'.lower():
    CURRENT_SCOPE = ConfigOption.HOME_PC

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