
from EnvSync.config.Remaps import *

import argparse
import sys

def findVimRcFile() -> str:

    homedir = os.path.expanduser('~')
    vimrc = os.path.join(homedir, '.vimrc')

    if not os.path.isfile(vimrc):

        # create empty vimrc file
        with open(vimrc, 'w') as f:
            f.write("")

    return vimrc

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

        vimrcContent: str = vimrc.toString(CURRENT_SCOPE | ConfigOption.NVIM)

        vim_rcPath = findVimRcFile()
        ConfigFile.writeToFile(vim_rcPath, vimrcContent)

    else:
        print(vimrc.toString(CURRENT_SCOPE), file=sys.stdout)

    exit(0)