
from __future__ import annotations
from EnvSync.config.ConfigFile import *

import argparse
import os
from EnvSync.utils import aspath

import re

import json
def readJsonFromFile(filePath: str) -> dict:
    with open(filePath, 'r') as file:
        return json.load(file)

import base64
def decrypt(encoded_message: str) -> str:

    base64_bytes = encoded_message.encode('utf-8')
    message_bytes = base64.b64decode(base64_bytes)
    return message_bytes.decode('utf-8')

CURRENT_FILE = os.path.abspath(__file__)

def initHomeTempFolder():

    if os.path.exists(TMP_FOLDER_PATH):
        return

    os.makedirs(TMP_FOLDER_PATH, exist_ok=False)

class Variable(ConfigOption):

    def __init__(self, value: str | Exec):

        super().__init__()
        self.isCommandOutput: bool = False
        self.name: str = None

        if isinstance(value, Exec):
            self.value: str = value.toString()
            self.isCommandOutput = True
        else:
            self.value: str = value

    def asCommandOutput(self):

        assert not self.isCommandOutput, "Variable is already a command output"
        self.isCommandOutput = True
        return self

    def withName(self, name: str):
        self.name = name
        return self

    def toString(self) -> str:

        if self.isCommandOutput:
            self.value = '$(' + self.value + ')'

        return f'{self.name}="{self.value}"'

class Path(Variable):

    def __init__(self, fileOrFolder: str):

        super().__init__(fileOrFolder)

        self.value = fileOrFolder
        self.name: str = None
        self.hasBeenGivenAlternate: bool = False
        self.isSharedOnGoogleDrive: bool = False

    def slash(self, otherPath):
        otherPath = Path(otherPath)
        return Path(os.path.join(self.value, otherPath.value)).withScope(self.scope)

    def asGoogleShared(self):

        assert not self.hasBeenGivenAlternate, "This folder has been given an alternate path, it cannot be shared on google drive"
        self.withScope(ConfigOption.COMMON)

        if not CURRENT_SCOPE == ConfigOption.LAPTOP:
            self.value = os.path.join(G_PAVILION_15, os.path.basename(self.value))

        return self

    def withAlternateValueForScope(self, scope, alternateValue: str | Path):

        assert not self.isSharedOnGoogleDrive, "This folder is shared on google drive, it cannot be given an alternate path"

        if CURRENT_SCOPE == scope:
            self.value = alternateValue.value if isinstance(alternateValue, Path) else alternateValue

        return self

    def toLinuxPath(self) -> str:
        # this function does not wrap the path with " quotes
        if not self.value:
            return ''

        return aspath.aslinuxPath(self.value, False)

    # override
    def toString(self) -> str:

        assert self.value, f"Path doesn't have value"
        assert self.name, f"Path doesn't have name: {self.value}"

        # assert os.path.exists(self.value), f"Path doesn't exist: {self.value}"
        if not os.path.exists(self.value):
            self.withComment('[WARNING] THIS PATH DOESNT EXIST')

        self.value = self.toLinuxPath()
        return super().toString()

class Exec(ConfigOption):

    def __init__(self, initialCommand: str | Path, aliasName: str = None):

        super().__init__()

        self.args: list[str] = []
        self.aliasName = aliasName

        if not initialCommand:
            return

        self.addCommand(initialCommand)

    def addCommand(self, command: str | Path | Exec):

        if isinstance(command, Path):
            command = command.value

        if isinstance(command, Exec):
            return self.addArgs(command.args)

        if isinstance(command, Function):
            return self.addArg(command.name)

        # command is str...

        if os.path.exists(command):
            self.addPath(command)
        else:
            self.addArg(command)

        return self

    def addArg(self, arg: str):
        arg = arg.strip()
        self.args.append(arg)
        return self

    def addExecOutput(self, command: Exec):
        return self.addArg(f'$({command.toString()})')

    def addQuoted(self, arg: str):

        arg = arg.strip('"')
        arg = arg.strip("'")

        arg = r"'\''" + arg
        arg = arg + r"'\''"

        return self.addArg(arg)

    def addArgs(self, args: list[str]):
        self.args.extend(args)
        return self

    def andThen(self, command: str):
        self.addArg('&&')
        return self.addCommand(command)

    def then(self, command: str):
        self.addArg(';')
        return self.addCommand(command)

    def ifFailed(self, command: str):
        self.addArg('||')
        return self.addCommand(command)


    def delay(self, seconds: int):
        return self.andThen(f'sleep {seconds}')

    def tee(self, command: str | Path = None):
        
        self.pipe('tee')
        self.addArg(f'>({command})')
        return self

    def inParallel(self, command: str | Path = None):

        while self.args and self.args[-1] == '&':
            self.args.pop()

        self.addArg('&')
        return self.addCommand(command) if command else self

    def disown(self):
        self.inParallel()
        return self.addArg('disown')

    def muteOutput(self, std: int = 3):

        assert std in [1, 2, 3]

        if std == 3:
            std = '&'

        return self.addArg(f'{std}> /dev/null')

    def addPath(self, p: Path | str):

        if isinstance(p, str): # overload function
            p = Path(p.strip())

        self.withScope(p.scope)

        linuxPath = p.toLinuxPath()
        if ' ' in linuxPath:
            linuxPath = '"' + linuxPath + '"'

        return self.addArg(linuxPath)

    def pipe(self, command: str | Exec):
        self.addArg('|')
        return self.addCommand(command)

    def grep(self, pattern: str):
        self.pipe('grep')
        self.addArg('-E')
        return self.addArg(pattern)

    # override
    def toString(self) -> str:

        if not self.aliasName:
            return " ".join(self.args)

        line = f"alias {self.aliasName}='"
        line += " ".join(self.args)
        line += "'"
        return line

class Alias(ConfigOption):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def to(self, exec: Exec | str) -> Exec:

        assert self.name, f'Name not specified for alias'

        if isinstance(exec, Path):
            exec = Exec(exec.value)

        if isinstance(exec, str) or isinstance(exec, Exec):
            exec = Exec(exec) # deep copy the exec

        self.scope = exec.scope
        exec.aliasName = self.name
        return exec

    # override
    def toString(self) -> str:
        raise NotImplementedError("Alias doesn't override toString() method, please bind to() an Exec")

class Function(ConfigOption):

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.executionLines: list[Exec] = []

    def addExecLine(self, exec: Exec | str):

        assert self.name, f'Name not specified for function'

        if isinstance(exec, str):
            exec = Exec(exec)

        self.executionLines.append(exec)
        return self
        
    def thenExecute(self, lines: list[Exec] | Exec | str):

        if isinstance(lines, str):
            return self.thenExecute([Exec(lines)])

        if isinstance(lines, Exec):
            return self.thenExecute([lines])

        assert isinstance(lines, list), 'Line isnt an Exec list type'

        for line in lines:
            self.addExecLine(line)

        return self

    # override
    def toString(self) -> str:

        res = f'{self.name}()\n'
        res += '{\n'

        for execLine in self.executionLines:
            res += f'\t{execLine.toString()}\n'

        res += '}\n'
        return res

class cdInto(Exec):

    def __init__(self, dir: Path | str):

        super().__init__('cd')
        self.addCommand(dir)
        self.tag = 'Directory Shortcuts'

class RunPython(Exec):

    def __init__(self, scriptPath: Path | str):

        super().__init__('python')
        self.addCommand(scriptPath)
        self.tag = 'Python scripts'

class InlinePython(RunPython):

    def __init__(self, runImmediately = False):
        super().__init__('-c')
        self.runImmediately = runImmediately

    def linesAre(self, lines: list[str]):

        if self.runImmediately:
            return self.addArg("'" + '; '.join(lines) + "'")
        else:
            return self.addQuoted('; '.join(lines))

class BashProfile(ConfigFile):

    def __init__(self):
        super().__init__()

    # override
    def commentChar(self) -> chr:
        return '#'

def runUnitTests():

    # Python
    assert RunPython(CURRENT_FILE).toString().__eq__(f'python {aspath.aslinuxPath(CURRENT_FILE)}')

    # Alias
    aliasRegexPattern = r'alias\s+\w+=["\'].*["\']'
    assert re.match(aliasRegexPattern, Alias('aliasName').to(RunPython('script.py')).toString())
    assert re.match(aliasRegexPattern, Alias('aliasName').to(cdInto('D:\\')).toString())

def findBashProfilePath() -> str:

    homeDir = os.path.expanduser('~')
    options = ['.bash_profile', '.bashrc', '.profile']

    for filename in options:

        fullPath = os.path.join(homeDir, filename)

        if os.path.exists(fullPath):
            return fullPath

    print("[WARN]: No bash profile file found in home directory.", file=sys.stderr)
    exit(0)
    return None

if __name__ == "__main__":

    # parse args
    parser = argparse.ArgumentParser(description='Update your bashprofile through Python')

    optionGroup = parser.add_mutually_exclusive_group()
    optionGroup.add_argument('--in_place', action='store_true', help='Directly modify ~/.bash_profile')
    optionGroup.add_argument('--force_scope', type=int, help='Mock run in a custom scope', required=False, default=CURRENT_SCOPE)

    args = parser.parse_args()
    if CURRENT_SCOPE != args.force_scope:
        CURRENT_SCOPE = args.force_scope

    # Run tests
    runUnitTests()

    # Paths
    D_DRIVE = Path("D:\\").withName('D Drive').withScope(ConfigOption.COMMON)
    C_DRIVE = Path("C:\\").withName('C Drive').withScope(ConfigOption.COMMON)

    REPO_ROOT = Path(REPO_ROOT).withName('REPO ROOT PATH')
    assert os.path.exists(REPO_ROOT.slash('.git').value), "Repo root does not contain .git folder"
    SRC_PATH = REPO_ROOT.slash('src').slash('envsync').withName('SRC PATH')
    UTILS_PATH = SRC_PATH.slash('utils').withName('UTILS PATH')

    G_DRIVE = Path("G:\\").withName('G Drive').withScope(ConfigOption.COMMON)
    ONEDRIVE_MUREX = Path("D:\\OneDrive - Murex").withName('ONEDRIVE').withScope(ConfigOption.MUREX)

    DESKTOP = Path(os.path.join(HOME_DIR, 'Desktop')).withName('DESKTOP').withScope(ConfigOption.LAPTOP).withAlternateValueForScope(ConfigOption.MUREX, ONEDRIVE_MUREX.slash('Desktop'))
    DOWNLOADS = Path(os.path.join(HOME_DIR, 'Downloads')).withName('DOWNLOADS').withScope(ConfigOption.LAPTOP).withAlternateValueForScope(ConfigOption.MUREX, ONEDRIVE_MUREX.slash('Downloads'))
    DOCUMENTS = Path('C:\\Users\\yyamm\\Documents\\MyDocuments').withName('DOCUMENTS').withScope(ConfigOption.LAPTOP).withAlternateValueForScope(ConfigOption.MUREX, os.path.join(G_PAVILION_15, 'MyDocuments'))

    MUREX_CLI = C_DRIVE.slash('murexcli').withScope(ConfigOption.MUREX)
    MUREX_SETTINGS_JSON = D_DRIVE.slash('.mxdevenvpp').slash('settings').slash('python_scripts_settings.json').withScope(ConfigOption.MUREX)

    murexSettings = dict()
    if CURRENT_SCOPE == ConfigOption.MUREX:
        murexSettings = readJsonFromFile(MUREX_SETTINGS_JSON.value)

    MUREX_SETTINGS_PY = MUREX_CLI.slash('settings.py').withScope(ConfigOption.MUREX)
    U_MXDEVENV = Path('U:\\tools\\mxdevenv\\mxdevenvpp').withScope(ConfigOption.MUREX)
    D_MXDEVENV = Path('D:\\.mxdevenvpp').withScope(ConfigOption.MUREX)
    REPO_MXDEVENV = Path('C:\\mxdevenv').withScope(ConfigOption.MUREX)

    UNMAP_DRIVES_SCRIPT = REPO_MXDEVENV.slash('Mxdevenvpp').slash('_Scripts').slash('mapsremove.bat').withScope(ConfigOption.MUREX)
    MAP_DRIVES_SCRIPT = REPO_MXDEVENV.slash('Mxdevenvpp').slash('_Scripts').slash('mapsFR.vbs').withScope(ConfigOption.MUREX)

    USERNAME = murexSettings.get('username', HOSTNAME)
    PASSWORD = murexSettings.get('password', None)

    CURRENT_VERSION = murexSettings.get('version', None)
    OLD_VERSION = murexSettings.get('previous_version', None)

    jqUpdateCommand = Exec('curl -L -o').addPath(os.path.join(BIN_DIR, 'jq.exe')).addArg('https://github.com/stedolan/jq/releases/latest/download/jq-win64.exe')
    updateGitBashCommand = Exec('git').addArg('update-git-for-windows')

    GQAF_SCRIPTS = MUREX_CLI.slash('gqaf').withScope(ConfigOption.MUREX)
    p4helperScript = RunPython(MUREX_CLI.slash('p4helper.py'))
    jiraScript = RunPython(MUREX_CLI.slash('JiraRequestHandler.py'))
    jenkinsScript = RunPython(MUREX_CLI.slash('JenkinsRequestHandler.py'))
    integrationScript = RunPython(MUREX_CLI.slash('IntegrationRequestHandler.py'))
    pasteScript = RunPython(UTILS_PATH.slash('paste.py')).withTag('Clipboard Utility')

    # Main script
    bashprofile: ConfigFile = BashProfile()
    bashprofile.options = [

    Alias('aspath').to(RunPython(UTILS_PATH.slash('aspath.py')).addArg('--from_stdin')).withTag(None),
    Alias('file').to('paste').pipe('aspath -linux').withTag(None),

    Alias('itunes').to('C:\\Program Files\\iTunes\\iTunes.exe').disown().withTag('iTunes').withScope(ConfigOption.LAPTOP),

    Alias('theplan').to('start').addPath(G_DRIVE.slash('My Drive').slash('THE_PLAN.xlsx')).withScope(ConfigOption.COMMON).withTag('Personal'),
    Alias('money').to(RunPython(UTILS_PATH.slash('FinanceManager').slash('parser.py'))).withTag('Personal'),
    Alias('updatemoney').to('money').addArg('--refresh').withTag('Personal'),

    Alias('grep').to('grep -i --color --binary-files=without-match').withTag('Grep default options'),
    Alias('grepdefects').to('grep').addArg('-Eo').addQuoted('DEF[0-9]+').withTag('grep').withScope(ConfigOption.MUREX),

    InlinePython(runImmediately=True).linesAre([
        'import pyautogui',
        'pyautogui.hotkey("win", "up")',
        'pyautogui.hotkey("ctrl", "+")',
        'pyautogui.hotkey("ctrl", "+")',
        'pyautogui.hotkey("ctrl", "+")',
    ]),

    cdInto(HOME_DIR).withScope(ConfigOption.LAPTOP).withTag("Init"),
    cdInto('D:\\').withScope(ConfigOption.MUREX).withTag("Init"),

    Alias('home').to(cdInto('~').withScope(ConfigOption.LAPTOP)),
    Alias('home').to('murexcli').withScope(ConfigOption.MUREX),
    Alias('src').to(cdInto(SRC_PATH)),
    Alias('back').to('cd').addArg('..').andThen('ls'),
    Alias('desk').to(cdInto(DESKTOP)),
    Alias('downloads').to(cdInto(DOWNLOADS)),
    Alias('docs').to(cdInto(DOCUMENTS)),

    Alias('music').to(cdInto('D:\\Music')).withScope(ConfigOption.LAPTOP),
    Alias('pics').to(cdInto('D:\\Camera Roll')).withScope(ConfigOption.LAPTOP),
    Alias('vids').to(cdInto('D:\\Videos')).withScope(ConfigOption.LAPTOP),
    Alias('movies').to(cdInto('D:\\Videos\\Movies')).withScope(ConfigOption.LAPTOP),

    # Alias('vim').to('nvim').withComment('nvim as default vim editor'),

    Alias('exp').to(RunPython(UTILS_PATH.slash('exp.py'))),
    Alias('start').to(RunPython(UTILS_PATH.slash('start.py'))),
    Alias('win').to(RunPython(UTILS_PATH.slash('win.py'))),

    Function('restart').thenExecute([
        Exec('win 2').disown(),
        Exec('exit'),
        ]).withTag('bash'),

    Alias('cat').to('bat').withTag('bash'),
    Alias('json').to('bat --language=json').withTag('bash'),
    Alias('csv').to('bat --language=csv').withTag('bash'),
    Alias(':r').to('restart').withTag('bash'),
    Alias(':q').to('win 2').andThen('exit').withTag('bash'),
    Alias('vimrc').to('code').addPath(os.path.join(HOME_DIR, '.vimrc')).withTag('bash'),
    Alias('bashprofile').to('code').addPath(os.path.join(HOME_DIR, '.bash_profile')).withTag('bash'),

    Alias('teeclip').to('tee').addArg(' >(clip)').withTag('bash'),
    Alias('first').to('head -n 1').withTag('bash'),
    Alias('recent').to('head -n 10').withTag('bash'),
    Alias('latest').to('tail -n 10').withTag('bash'),
    Alias('last').to('tail -n 1').withTag('bash'),

    Function('color').thenExecute([
        Exec('grep').addArg('--color').addArg('-E').addArg('"$1|^"'),
        ]).withTag('Grep color'),

    Function('col').thenExecute([
        Exec('awk').addArg('-v column="$1"').addArg("'{print $column}'"),
        ]).withTag('awk shortcut'),

    Function('cdl').thenExecute([
        cdInto('"$1"').andThen('ls'),
        ]).withTag('Quick cd'),

    Alias('editvimrc').to('code').addPath(os.path.join(CURRENT_DIR, 'VimRC.py')).withTag('Config'),
    Alias('editbashprofile').to('code').addPath(CURRENT_FILE).withTag('Config'),
    Alias('editnvim').to('vim').addPath(NVIM_RC).withTag('Config'),
    Alias('runbashprofile').to(RunPython(CURRENT_FILE)).withTag('Config'),

    Function('updatebashprofile').thenExecute([
        Exec('echo Updating...'),
        Exec(RunPython(CURRENT_FILE).addArg('--in_place'))
        ]).withTag('Config'),

    Alias('switch').to(InlinePython().linesAre([
        'import pyautogui',
        'pyautogui.hotkey("alt", "tab")'
    ])).withTag('Quick Automations'),

    Function('updatevimrc').thenExecute([
        Exec('echo Updating...'),
        Exec(RunPython(SRC_PATH.slash('config').slash('VimRC.py')).addArg('--in_place')),
        Exec('echo Done.'),
        ]).withTag('Config'),

    Alias('path').to('echo $PATH').pipe('tr').addArg('":"').addArg(r'"\n"').pipe('sort -u').withTag('OS'),
    Alias('cls').to('clear').then('jobs').withTag('OS'),
    Alias('cmd').to('start').addPath('C:\\Windows\\System32\\cmd.exe').withTag('OS'),
    Alias('connected').to('curl -s www.google.com').muteOutput().withTag('OS'),
    Alias('checkConnection').to('connected').then('echo $?').withTag('OS'),
    Alias('size').to(RunPython(UTILS_PATH.slash('size.py'))).withTag('OS'),

    Alias('tm').to(InlinePython().linesAre([
        'import pyautogui',
        'pyautogui.hotkey("ctrl", "shift", "esc")'
    ])).withTag('Windows'),

    Alias('greppaste').to('grep').addArg('"$(paste)"').withTag('Quick Grep'),
    Alias('gp').to('greppaste').withTag('Quick Grep'),

    Alias('cdpaste').to(cdInto('"$(paste | aspath -linux)"')),
    Alias('vimpaste').to('paste').pipe('vim -').withTag('Vim'),
    Alias('vimfile').to('vim').addExecOutput(Exec('file')).withTag('Vim'),
    Alias('pastevim').to('paste').pipe('vim -').withTag('Vim'),

    Alias('gs').to('git status').withTag('Git'),
    Alias('gd').to('git diff').withTag('Git'),
    Alias('gln').to('git log -n').withTag('Git'),

    Alias('netpass').to(RunPython(SRC_PATH.slash('NetPass').slash('netpass.py'))),

    Alias('jq').to(os.path.join(BIN_DIR, 'jq.exe')).withTag('JSON Query'),

    Function('updatejq').thenExecute([
        jqUpdateCommand,
        Exec('echo').withComment('new line'),
        Exec('alias jq'),
        Exec('echo').withComment('new line'),
        Exec('jq').addArg('--version'),
        ]).withTag('JSON Query'),

    Alias('updategitbash').to(updateGitBashCommand).withTag('Update Git Bash'),

    Alias('count').to('wc').addArg('-l').withTag('Quick count lines'),

    Alias('copy').to('clip').withTag('Clipboard'),
    Alias('paste').to(pasteScript).pipe('tr -d').addArg(r'"\r"').withTag('Clipboard'),

    Alias('settings').to('code').addPath(MUREX_SETTINGS_JSON).withScope(ConfigOption.MUREX).withTag('MxSettings'),

    Variable(CURRENT_VERSION).withName('VERSION').withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Variable(OLD_VERSION).withName('OLD_VERSION').withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('allMxVersions').to(RunPython(GQAF_SCRIPTS.slash('allMxVersions.py'))).withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('version').to('echo $VERSION').withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('versionUpgrade').to(RunPython(DOWNLOADS.slash('scripts').slash('upgradeVersion.py'))).withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('richVersionView').to(RunPython(MUREX_CLI.slash('gqaf').slash('richVersionView.py'))).withScope(ConfigOption.MUREX).withTag('Status'),
    Alias('richVersionViewCsv').to('richVersionView').addArg('--csv').addArg('> tmp.csv').andThen('start tmp.csv').withScope(ConfigOption.MUREX).withTag('Status'),
    Alias('safetyNetStatus').to(RunPython(MUREX_CLI.slash('gqaf').slash('safetyNetStatus.py'))).withScope(ConfigOption.MUREX).withTag('Status'),
    Alias('oldversion').to('echo $OLD_VERSION').withScope(ConfigOption.MUREX).withTag('MxVersion'),

    Alias('clipVersion').to('version').tee('clip').andThen('echo Copied.').withScope(ConfigOption.MUREX).withTag('MxVersion'),

    Alias('cdversion').to(cdInto('/d/$(version)')).withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('startversion').to('start').addArg('/d/$(version)/mx-$(version).sln.lnk').withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('startbpversion').to('start').addArg('/d/$(bpversion)/mx-$(bpversion).sln.lnk').withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('cdapps').to(cdInto('/d/apps')).withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('appsversion').to(cdInto('/d/apps/$(version)*')).withScope(ConfigOption.MUREX).withTag('MxVersion'),

    Variable(Exec('jq .backport_version -r <').addPath(MUREX_SETTINGS_JSON)).withName('BPVERSION').withScope(ConfigOption.MUREX).withTag('Backport'),
    Alias('bpversion').to('echo $BPVERSION').withScope(ConfigOption.MUREX).withTag('Backport'),
    Alias('cdbpversion').to(cdInto('/d/$(bpversion)')).withScope(ConfigOption.MUREX).withTag('Backport'),

    Exec(f'echo Hello {USERNAME}!').withScope(ConfigOption.MUREX).withTag('Welcome message'),
    Exec('echo You are on ALIEN version').addArg('$(version)').withScope(ConfigOption.MUREX).withTag('Welcome message'),
    Exec('echo -e \n').withScope(ConfigOption.MUREX).withTag('Welcome message'),
    Exec(p4helperScript).addArg('--unmerged').muteOutput(2).withScope(ConfigOption.MUREX).withTag('Welcome message'),
    Exec('ls /u').muteOutput(3).ifFailed('echo "[WARNING]: Drives aren\'t mapped!"').withScope(ConfigOption.MUREX).withTag('Welcome message'),

    Alias('p4helper').to(p4helperScript).withScope(ConfigOption.MUREX).withTag('Perforce P4'),
    Alias('psubmit').to('p4helper').addArg('--submit').addArg('$(paste)').withScope(ConfigOption.MUREX).withTag('Perforce P4'),
    Alias('jira').to(jiraScript).withScope(ConfigOption.MUREX).withTag('Jira Request Handler'),
    Alias('jenkins').to(jenkinsScript).withScope(ConfigOption.MUREX).withTag('Jenkins Request Handler'),
    Alias('integrate').to(integrationScript).withScope(ConfigOption.MUREX).withTag('Integration Handler'),

    Alias('submit').to('p4helper --submit').withScope(ConfigOption.MUREX).withTag('Create a perfoce changelist from jira ID'),
    Alias('isItMerged').to('echo "looking for $(paste)..."').andThen('p4helper --me --build').pipe('greppaste').withScope(ConfigOption.MUREX).withTag('Quick check if defect is in mainstream'),

    Alias('mxbot').to('start').addArg(f'https://integrationweb.gqaf.fr.murex.com').withScope(ConfigOption.MUREX).withTag('Open MxBot Integration link'),
    Alias('ci').to('start').addArg(f'https://cje-core.fr.murex.com/assets/job/CppValidation/job/{CURRENT_VERSION}/').withScope(ConfigOption.MUREX).withTag('Open CI pipeline link'),
    Alias('freyja').to('start').addArg(f'https://cje-core.fr.murex.com/assets/job/FreyjaAlien/job/{CURRENT_VERSION}/').withScope(ConfigOption.MUREX).withTag('Open CI pipeline link'),

    Alias('mxOpen').to(RunPython(DOWNLOADS.slash('scripts').slash('mxOpen.py'))).withScope(ConfigOption.MUREX).withTag('MxOpen'),
    Alias('coco').to(RunPython(DOWNLOADS.slash('scripts').slash('mxOpen.py'))).addArg('--coconut').withScope(ConfigOption.MUREX).withTag('Search Coconut'),

    Alias('auth').to(RunPython(DOWNLOADS.slash('scripts').slash('auth.py'))).withScope(ConfigOption.MUREX).withTag('Auto Auth'),

    Alias('mde').to('D:\\.mxdevenvpp\\bin\\mde++.cmd').withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('mdeversion').to('mde about').pipe('grep -o').addArg('^0.[0-9]*.0.[0-9]*').withScope(ConfigOption.MUREX).withTag('Mxdevenv'),

    Alias('mdelatest').to(U_MXDEVENV.slash('latest').slash('mde++.cmd')).withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('mdelatestversion').to('mdelatest about').pipe('grep -o').addArg('^0.[0-9]*.0.[0-9]*').withScope(ConfigOption.MUREX).withTag('Mxdevenv'),

    Alias('umxdevenv').to(cdInto(U_MXDEVENV)).withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('dmxdevenv').to(cdInto(D_MXDEVENV)).withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('repomxdevenv').to(cdInto(REPO_MXDEVENV)).withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('murexcli').to(cdInto(MUREX_CLI)).withScope(ConfigOption.MUREX).withTag('Mxdevenv'),

    Alias('prepareVersion').to('mde prepareVersion').withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('prepareVersionFromClipBoard').to('mde prepareVersion -v $(paste) &').withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('versionManager').to('mde versionManager').inParallel().withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('logsVisualizer').to('mde logsVisualizer').inParallel().withScope(ConfigOption.MUREX).withTag('Mxdevenv'),
    Alias('setupsViewer').to('mde setupsViewer').withScope(ConfigOption.MUREX).withTag('Mxdevenv'),

    Alias('revertfile').to(InlinePython().linesAre([
        'import pyautogui',
        'pyautogui.PAUSE = 0.1',
        'pyautogui.hotkey("win", "3")',
        'pyautogui.press("esc", 5)',
        'pyautogui.press("alt")',
        'pyautogui.press("x")',
        'pyautogui.press("enter")',
        'pyautogui.press("down", 9)',
        'pyautogui.press("right")',
        'pyautogui.press("down", 3)',
        'pyautogui.press("enter")',
    ])).withScope(ConfigOption.MUREX).withTag('Quick Automations'),

    Alias('debugme').to('/d/apps/$(version)*/debugMe++.cmd').inParallel().withScope(ConfigOption.MUREX).withTag('Debugging'),
    Alias('debugmebackport').to('/d/apps/$(bpversion)*/debugMe++.cmd').inParallel().withScope(ConfigOption.MUREX).withTag('Debugging'),

    Alias('drivesmapped').to('[ -d "/u" ]').then('echo $?').withScope(ConfigOption.MUREX).withTag('Drive Mapping'),
    Alias('unmapdrives').to('start').addPath(UNMAP_DRIVES_SCRIPT).withScope(ConfigOption.MUREX).withTag('Drive Mapping'),
    Alias('mapdrives').to('unmapdrives').delay(1).andThen('start').addPath(MAP_DRIVES_SCRIPT).delay(0.5).andThen('ls /u').withScope(ConfigOption.MUREX).withTag('Drive Mapping'),

    Alias('sessionInfo').to(RunPython(MUREX_CLI.slash('SessionInfo.py'))).withScope(ConfigOption.MUREX).withTag('Murex Session Info'),

    Alias('setups').to(RunPython(GQAF_SCRIPTS.slash('setups.py'))).withScope(ConfigOption.MUREX).withTag('GQAF API'),
    Alias('setupscsv').to('setups --csv 2>&1').grep('-vE').addQuoted(r'^getting|^fetching|^[0-9]|^\s*$').pipe('sed').addQuoted(r's/\s*,\s*/,/g').addArg('> tmp.csv && start tmp.csv').withScope(ConfigOption.MUREX).withTag('GQAF API'),
    Alias('pushsetups').to(RunPython(GQAF_SCRIPTS.slash('pushsetups.py'))).withScope(ConfigOption.MUREX).withTag('GQAF API'),
    Alias('pushsetupsAtHead').to('pushsetups').addArg('--head').addArg('--linux').withScope(ConfigOption.MUREX).withTag('GQAF API'),
    Alias('pushJobs').to(RunPython(GQAF_SCRIPTS.slash('pushJobs.py'))).withScope(ConfigOption.MUREX).withTag('GQAF API'),
    Alias('tpks').to(RunPython(GQAF_SCRIPTS.slash('jobs.py'))).withScope(ConfigOption.MUREX).withTag('GQAF API'),

    Alias('dtk').to('start').addPath('D:\\tools\\dtk\\tk.3.rc.1\\toolkit.bat').withScope(ConfigOption.MUREX).withTag('DTK'),

    cdInto(MUREX_CLI).withTag('Starting dir').withScope(ConfigOption.MUREX),
    cdInto(SRC_PATH).withTag('Starting dir').withScope(ConfigOption.LAPTOP),

    ]

    if args.in_place:
        bashprofileContent: str = bashprofile.toString(scopeFilter=CURRENT_SCOPE)
        ConfigFile.writeToFile(findBashProfilePath(), bashprofileContent)
    else:
        print(bashprofile.toString(), file=sys.stdout)