
from EnvSync.config.ConfigFile import ConfigFile, ConfigOption
import os

CURRENT_FILE = os.path.abspath(__file__)

class VimOption(ConfigOption):

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.tag = 'Options'

    # override
    def toString(self) -> str:
        return f"set {self.name}"

class VimMacro(ConfigOption):

    def __init__(self):
        super().__init__()
        self.tag = "Macros"
        self.command = None
        self.letter = None

    def mapLetter(self, letter: chr):
        
        self.letter = letter
        return self

    def withAction(self, command: str):
        
        self.command = command
        return self

    # override
    def toString(self) -> str:

        assert self.letter and self.command, "macro is not properly set"
        res = f"let @{self.letter} = '{self.command}'"
        return res

class VimRemap(ConfigOption):

    INSERT = 0
    VISUAL = 1
    NORMAL = 2
    BOTH = 3

    remapOptionLetter: dict[int, chr] = {INSERT:'i', NORMAL:'n', VISUAL:'v'}
    centerOffset = 12
    pageOffset = 10

    def __init__(self):

        super().__init__()

        self.left = None
        self.right = None

        self.mode = None

        self.recursive = False

        self.centerOffset= False
        self.centerMiddle= False

    def remap(self, left: str, right: str):

        assert not self.isReady(), "cannot set remap command twice"

        self.left = left
        self.right = right
        return self

    def remapLeader(self, left: str, right: str):

        assert not self.isReady(), "cannot set remap command twice"

        self.left = f'<leader>{left}'
        self.right = right
        return self

    def withRecursion(self, r = True):

        self.recursive = r
        return self

    def thenCenterWithOffset(self):

        self.centerOffset = True
        return self

    def thenCenterMiddle(self):

        self.centerMiddle = True
        return self

    def forMode(self, mode: int):

        self.mode = mode
        return self

    def isReady(self) -> bool:
        
        if self.left is None:
            return False

        if self.right is None:
            return False

        if self.mode is None:
            return False

        return True

    # override
    def toString(self) -> str:
        
        assert self.isReady(), "remap not set properly"

        line: str = VimRemap.remapOptionLetter.get(self.mode, "")

        if not self.recursive:
            line += "no"
        line += "remap"

        if self.centerMiddle:
            self.right = self.right + f'zz'
        elif self.centerOffset:
            self.right = self.right + f'{VimRemap.centerOffset}jzz{VimRemap.centerOffset}k'

        line += f" {self.left} {self.right}"

        if self.mode == VimRemap.BOTH:
            line2 = line
            line = self.remapOptionLetter[VimRemap.NORMAL] + line
            line2 = self.remapOptionLetter[VimRemap.VISUAL] + line2
            return line + "\n" + line2

        return line

class VimRC(ConfigFile):

    def __init__(self, leaderKey: str = None):

        super().__init__()
        self.leaderKey = leaderKey

    def setLeaderKey(self, leaderKey: str):
        self.leaderKey = leaderKey

    # override
    def commentChar(self) -> str:
        return '"'

    # override
    def toString(self, scopeFilter):

        if not self.leaderKey:
            return super().toString(scopeFilter)

        res = f'\nlet mapleader = "{self.leaderKey}"'
        res += "\n"
        return res + super().toString(scopeFilter)