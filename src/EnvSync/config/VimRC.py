
from EnvSync.config.ConfigFile import *
import argparse

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
    def toString(self, scopeFilter = CURRENT_SCOPE):

        if not self.leaderKey:
            return super().toString(scopeFilter)

        res = f'\nlet mapleader = "{self.leaderKey}"'
        res += "\n"
        return res + super().toString(scopeFilter)

if __name__ == "__main__":

    VimRemap.centerOffset = 12
    VimRemap.pageOffset = 10

    vimrc: ConfigFile = VimRC()
    vimrc.setLeaderKey(r'\<Space>')
    vimrc.options = [

    VimOption('relativenumber'),
    VimOption('ignorecase'),
    VimOption('nowrap'),

    VimRemap().remapLeader('p', '"_dP').forMode(VimRemap.VISUAL).withTag('Lazy Paste'),
    VimRemap().remapLeader('w', ':w<CR>').forMode(VimRemap.NORMAL).withTag('Quick Save'),
    VimRemap().remapLeader('q', '<Esc>:q<CR>').forMode(VimRemap.BOTH).withTag('Quick Quit'),
    VimRemap().remapLeader('e', '<Esc>:e!<CR>').forMode(VimRemap.BOTH).withTag('Quick Reset'),

    VimRemap().remapLeader('y', '"+y').forMode(VimRemap.VISUAL).withTag('System clipboard'),
    VimRemap().remapLeader('v', '"+p').forMode(VimRemap.VISUAL).withTag('System clipboard'),
    VimRemap().remapLeader('d', 'Vd').forMode(VimRemap.NORMAL).withTag('System clipboard'),
    VimRemap().remap('<C-p>', '"+p').forMode(VimRemap.BOTH).withTag('System clipboard'),

    VimRemap().remap('H', '0^').forMode(VimRemap.BOTH).withTag('Horizontal Movement'),
    VimRemap().remap('L', '$').forMode(VimRemap.BOTH).withTag('Horizontal Movement'),
    VimRemap().remap(',', ';').forMode(VimRemap.BOTH).withTag('Horizontal Movement'),
    VimRemap().remap(';', ',').forMode(VimRemap.BOTH).withTag('Horizontal Movement').withComment('Swap f next/previous'),

    VimRemap().remap('zz', 'zz').forMode(VimRemap.BOTH).thenCenterWithOffset().withTag('Centering').withComment('Center at top of page'),
    VimRemap().remap('n', 'n').forMode(VimRemap.NORMAL).thenCenterMiddle().withTag('Centering'),
    VimRemap().remap('N', 'N').forMode(VimRemap.NORMAL).thenCenterMiddle().withTag('Centering'),
    VimRemap().remap('*', '*').forMode(VimRemap.NORMAL).thenCenterMiddle().withTag('Centering'),
    VimRemap().remap('#', '#').forMode(VimRemap.NORMAL).thenCenterMiddle().withTag('Centering'),
    VimRemap().remap('<C-o>', '<C-o>').forMode(VimRemap.NORMAL).thenCenterMiddle().withTag('Centering'),
    VimRemap().remap('<C-i>', '<C-i>').forMode(VimRemap.NORMAL).thenCenterMiddle().withTag('Centering'),

    VimRemap().remap('<C-d>', f'{VimRemap.pageOffset}j^').forMode(VimRemap.NORMAL).thenCenterMiddle().withTag('Page up down'),
    VimRemap().remap('<C-u>', f'{VimRemap.pageOffset}k^').forMode(VimRemap.NORMAL).thenCenterMiddle().withTag('Page up down'),

    VimRemap().remap('<C-l>', 'f(').forMode(VimRemap.BOTH).withTag('Parentheses Movement'),
    VimRemap().remap('<C-H>', '%').forMode(VimRemap.BOTH).withTag('Parentheses Movement'),

    VimRemap().remap('za', 'za').forMode(VimRemap.BOTH).thenCenterMiddle().withTag('Folding'),
    VimRemap().remap('gd', 'gdzzzo').forMode(VimRemap.BOTH).thenCenterWithOffset().withTag('Folding').withComment("Jump to definition then unfold"),
    VimRemap().remap('gd', 'gdzzzo').forMode(VimRemap.BOTH).thenCenterWithOffset().withTag('Folding').withComment("Jump to definition then unfold"),

    VimMacro().mapLetter('f').withAction('va{%kv^zz').withComment('Go up 1 C++ bracket level'),

    ]

    parser = argparse.ArgumentParser(description='Update your bashprofile through Python')

    parser.add_argument('--in_place', action='store_true', help='directly modify ~/.vimrc')
    args = parser.parse_args()

    if args.in_place:

        nvimrcContent: str = vimrc.toString(CURRENT_SCOPE | ConfigOption.NVIM)
        ConfigFile.writeToFile(NVIM_RC, nvimrcContent)

        vimrcContent: str = vimrc.toString(CURRENT_SCOPE | ConfigOption.NVIM)
        ConfigFile.writeToFile(VIM_RC, vimrcContent)

    else:
        print(vimrc.toString(CURRENT_SCOPE), file=sys.stdout)