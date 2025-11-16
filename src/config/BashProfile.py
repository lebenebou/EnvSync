
import os
import sys
import argparse

from GlobalEnv import GlobalEnv, ConfigScope
from config.Aliases import *

CURRENT_FILE = os.path.abspath(__file__)

import json
def readJsonFromFile(filePath: str) -> dict:

    assert os.path.isfile(filePath), f"File does not exist: {filePath}"

    with open(filePath, 'r') as file:
        return json.load(file)

def mxdevenvOptions() -> list[ConfigOption]:

    mxdevenvRepoPath = 'C:\\mxdevenv'
    mxdevenvUtilityScriptsPath = os.path.join(mxdevenvRepoPath, 'Mxdevenvpp', '_Scripts')

    options: list[ConfigOption] = [

    Alias('mde').to('D:\\.mxdevenvpp\\bin\\mde++.cmd').withTag('mxdevenv runners'),
    Alias('mde++').to('D:\\.mxdevenvpp\\bin\\mde++.cmd').withTag('mxdevenv runners'),
    Alias('mdeversion').to('mde about').pipe('grep -o').addArg('^0.[0-9]*.0.[0-9]*').withTag('mxdevenv runners'),

    # path shortcuts
    Alias('umxdevenv').to(cdInto('U:\\tools\\mxdevenv\\mxdevenvpp')).withTag('mxdevenv path shortcuts'),
    Alias('dmxdevenv').to(cdInto('D:\\.mxdevenvpp')).withTag('mxdevenv path shortcuts'),
    Alias('repomxdevenv').to(cdInto(mxdevenvRepoPath)).withTag('mxdevenv path shortcuts'),

    # version management
    Alias('prepareVersionFromClipBoard').to('mde prepareVersion -v $(paste) &').withTag('MxVersion Management'),
    Alias('versionManager').to('mde versionManager').inParallel().withTag('MxVersion Management'),

    # logbook
    Alias('logsVisualizer').to('mde logsVisualizer').inParallel().withTag('Logbook'),

    # debugging
    Alias('debugme').to('/d/apps/$(version)*/debugMe++.cmd').inParallel().withTag('DebugMe++'),

    # drive mapping
    Alias('drivesmapped').to('[ -d "/u" ]').then('echo $?').withTag('Drive Mapping'),
    Alias('unmapdrives').to('start').addPath(os.path.join(mxdevenvUtilityScriptsPath, 'mapsremove.bat')).withTag('Drive Mapping'),
    Alias('mapdrives').to('unmapdrives').delay(1).andThen('start').addPath(os.path.join(mxdevenvUtilityScriptsPath, 'mapsFR.vbs')).delay(0.5).andThen('ls /u').withTag('Drive Mapping'),

    ]

    for option in options:
        option.withScope(ConfigScope.MUREX)

    return options

def mxVersionManagementOptions() -> list[ConfigOption]:

    D_DRIVE = Path("D:\\")
    murexSettingsJsonPath = os.path.join('D:\\', '.mxdevenvpp', 'settings', 'python_scripts_settings.json')

    murexSettings = dict()
    if globalEnv.currentScope & ConfigScope.MUREX:
        murexSettings = readJsonFromFile(murexSettingsJsonPath)

    CURRENT_VERSION = murexSettings.get('version', None)
    OLD_VERSION = murexSettings.get('previous_version', None)

    options: list[ConfigOption] = [

    # MxVersion
    Alias('version').to(f'echo {CURRENT_VERSION}').withTag('MxVersion'),
    Alias('clipVersion').to('version').tee('clip').andThen('echo Copied.').withTag('MxVersion'),
    Alias('oldversion').to(f'echo {OLD_VERSION}').withTag('MxVersion'),

    # MxVersion manipulation
    Alias('cdversion').to(cdInto('/d/$(version)')).withTag('MxVersion Manipulation'),
    Alias('startversion').to('start').addArg('/d/$(version)/mx-$(version).sln.lnk').withTag('MxVersion Manipulation'),
    Alias('cdapps').to(cdInto('/d/apps/$(version)*')).withTag('MxVersion Manipulation'),
    Alias('versionUpgrade').to(RunPython(D_DRIVE / 'Personal' / 'scripts' / 'upgradeVersion.py')).withTag('MxVersion Manipulation'),

    Alias('settings').to('vim').addPath(murexSettingsJsonPath),

    ]

    for option in options:
        option.withScope(ConfigScope.MUREX)

    return options

def murexLinkShortcuts() -> list[ConfigOption]:

    options: list[ConfigOption] = [

    Alias('mxbot').to(OpenLink(f'https://integrationweb.gqaf.fr.murex.com')),
    Alias('ci').to(OpenLink(f'https://cje-core.fr.murex.com/assets/job/Alien/job/Git%20Alien/job/Git%20cpp%20build/')),
    Alias('pullRequest').to(OpenLink(f'https://stash.murex.com/projects/ASSETS/repos/alien/pull-requests?create')),

    ]

    for option in options:
        option.withScope(ConfigScope.MUREX)
        option.withTag('Murex Link Shortcuts')

    return options

def murexWelcomeMessage() -> list[ConfigOption]:

    p4helperScript = RunPython('C:\\murexcli\\p4helper.py')

    options: list[ConfigOption] = [

    Exec(f'echo Hello yoyammine!'),
    Exec('echo You are on ALIEN version').addArg('$(version)'),
    Exec('echo -e \n'),
    Exec(p4helperScript).addArg('--unmerged'),
    Exec('ls /u').muteOutput(3).ifFailed('echo "[WARNING]: Drives aren\'t mapped!"'),

    ]

    for option in options:

        if isinstance(option, Exec): option.onlyIfThroughGitBash()
        option.withScope(ConfigScope.MUREX)
        option.withTag('Welcome message')

    return options

def murexCliOptions() -> list[ConfigOption]:

    MUREX_CLI = (C_DRIVE / 'murexcli').withScope(ConfigScope.MUREX)

    # Murex scripts
    GQAF_SCRIPTS = (MUREX_CLI / 'gqaf').withScope(ConfigScope.MUREX)
    p4helperScript = RunPython(MUREX_CLI / 'p4helper.py').withScope(ConfigScope.MUREX)
    jiraScript = RunPython(MUREX_CLI / 'JiraRequestHandler.py').withScope(ConfigScope.MUREX)
    jenkinsScript = RunPython(MUREX_CLI / 'JenkinsRequestHandler.py').withScope(ConfigScope.MUREX)
    integrationScript = RunPython(MUREX_CLI / 'IntegrationRequestHandler.py').withScope(ConfigScope.MUREX)

    options: list[ConfigOption] = [

    # Session info
    Alias('sessionInfo').to(RunPython(MUREX_CLI / 'SessionInfo.py')).withTag('Session Info'),

    Alias('murexcli').to(cdInto(MUREX_CLI)),

    Alias('displayAlien').to(RunPython(MUREX_CLI / 'display_alien' / 'excel_refresher.py')\
                             .andThen('start').addPath(MUREX_CLI / 'display_alien' / 'display_alien.xlsx')),

    # P4 Helpers
    Alias('p4helper').to(p4helperScript).withTag('P4 Helpers'),
    Alias('psubmit').to('p4helper').addArg('--submit').addArg('$(paste)').withTag('P4 Helpers'),
    Alias('submit').to('p4helper --submit').withTag('P4 Helpers'),
    Alias('isItMerged').to('echo "looking for $(paste)..."').andThen('p4helper --me --build').pipe('greppaste').withTag('P4 Helpers'),
    Alias('dtk').to('start').addPath('D:\\tools\\dtk\\tk.3.rc.1\\toolkit.bat').withTag('P4 Helpers'),

    # Jira
    Alias('jira').to(jiraScript).withTag('Jira Helpers'),

    # Jenkins
    Alias('jenkins').to(jenkinsScript).withTag('Jenkins Helpers'),
    Alias('integrate').to(integrationScript).withTag('Jenkins Helpers'),

    Alias('grepdefects').to('grep').addArg('-Eo').addQuoted('DEF[0-9]+'),

    # Personal scripts
    Alias('mxOpen').to(RunPython(D_DRIVE / 'Personal' / 'scripts' / 'mxOpen.py')).withTag('Personal Scripts'),
    Alias('coco').to(RunPython(D_DRIVE / 'Personal' / 'scripts' / 'mxOpen.py')).addArg('--coconut').withTag('Personal Scripts'),
    Alias('auth').to(RunPython(D_DRIVE / 'Personal' / 'scripts' / 'auth.py')).withTag('Personal Scripts'),

    # GQAF scripts
    Alias('setups').to(RunPython(GQAF_SCRIPTS / 'setups.py')).withTag('GQAF Setups'),
    Alias('pushsetups').to(RunPython(GQAF_SCRIPTS / 'pushsetups.py')).withTag('GQAF Setups'),
    Alias('pushsetupsAtHead').to('pushsetups').addArg('--head').addArg('--linux').withTag('GQAF Setups'),

    Alias('safetyNetStatus').to(RunPython(MUREX_CLI / 'gqaf' / 'safetyNetStatus.py')).withTag('GQAF Scripts'),

    Alias('richVersionView').to(RunPython(MUREX_CLI / 'gqaf' / 'richVersionView.py')).withTag('GQAF Scripts'),
    Alias('richVersionViewCsv').to('richVersionView').addArg('--csv').addArg('> tmp.csv').andThen('start tmp.csv').withTag('GQAF Scripts'),

    Alias('tpks').to(RunPython(GQAF_SCRIPTS / 'jobs.py')).withTag('GQAF Scripts'),
    Alias('allMxVersions').to(RunPython(GQAF_SCRIPTS / 'allMxVersions.py')).withTag('GQAF Scripts'),

    ]

    for option in options:
        option.withScope(ConfigScope.MUREX)

    return options

if __name__ == "__main__":

    globalEnv = GlobalEnv()

    # parse args
    parser = argparse.ArgumentParser(description='Update your bashprofile through Python')

    optionGroup = parser.add_mutually_exclusive_group()
    optionGroup.add_argument('-i', '--in_place', action='store_true', help='Directly modify ~/.bash_profile')

    args = parser.parse_args()

    # Windows drives
    D_DRIVE = Path("D:\\").withName('D Drive').withScope(ConfigScope.WINDOWS)
    C_DRIVE = Path("C:\\").withName('C Drive').withScope(ConfigScope.WINDOWS)
    G_DRIVE = Path("G:\\").withName('G Drive').withScope(ConfigScope.WINDOWS)
    ONEDRIVE_MUREX = (D_DRIVE / "OneDrive - Murex").withName('ONEDRIVE').withScope(ConfigScope.MUREX | ConfigScope.WINDOWS)

    # Repo paths
    envSyncRepoPath = Path(globalEnv.repoRootPath).withName('REPO ROOT PATH')
    envSyncSrcPath = Path(globalEnv.repoSrcPath).withName('SRC PATH')
    UTILS_PATH = (envSyncSrcPath / 'utils').withName('UTILS PATH')

    # User folders
    DESKTOP = Path(os.path.join(globalEnv.userHomeDir, 'Desktop')).withName('DESKTOP').withScope(ConfigScope.LAPTOP | ConfigScope.LINUX)
    DOWNLOADS = Path(os.path.join(globalEnv.userHomeDir, 'Downloads')).withName('DOWNLOADS').withScope(ConfigScope.LAPTOP)
    DOCUMENTS = Path('C:\\Users\\yyamm\\Documents\\MyDocuments').withName('DOCUMENTS').withScope(ConfigScope.LAPTOP)

    # User variables
    USERNAME = globalEnv.hostname

    if globalEnv.currentScope & ConfigScope.MUREX:

        DESKTOP = (ONEDRIVE_MUREX / 'Desktop').withScope(ConfigScope.MUREX)
        DOWNLOADS = (ONEDRIVE_MUREX / 'Downloads').withScope(ConfigScope.MUREX)
        DOCUMENTS = (ONEDRIVE_MUREX / 'Documents').withScope(ConfigScope.MUREX)

        USERNAME = 'yoyammine'

    if globalEnv.currentScope & ConfigScope.LINUX:
        DOCUMENTS = Path(os.path.join(globalEnv.userHomeDir, 'Documents')).withName('DOCUMENTS').withScope(ConfigScope.LINUX)

    # clipboard utilities
    copy = RunPython(UTILS_PATH / 'clipboard.py').addArg('--copy').withTag('Clipboard Utility')
    paste = RunPython(UTILS_PATH / 'clipboard.py').addArg('--paste').withTag('Clipboard Utility')

    updateGitBash = Exec('git').addArg('update-git-for-windows').withScope(ConfigScope.WINDOWS)

    # Main script
    bashprofile: ConfigFile = BashProfile()
    bashprofile.options = [

    Alias('aspath').to(RunPython(UTILS_PATH / 'aspath.py').addArg('--from_stdin')),

    Alias('theplan').to('start').addPath(G_DRIVE / 'My Drive' / 'THE_PLAN.xlsx').withScope(ConfigScope.WINDOWS).withTag('Personal'),
    Alias('money').to(RunPython(envSyncSrcPath / 'finance' / 'main.py')).withTag('Personal'),

    Alias('grep').to('grep -i --color --binary-files=without-match --exclude-dir=".git"').withTag('Grep Options'),
    Alias('greppaste').to('grep').addArg('"$(paste)"').withTag('Grep Options'),

    InlinePython(runImmediately=True).linesAre([
        'import pyautogui',
        'pyautogui.hotkey("win", "up")',
        'pyautogui.hotkey("ctrl", "+")',
        'pyautogui.hotkey("ctrl", "+")',
        'pyautogui.hotkey("ctrl", "+")',
    ]).onlyIfThroughGitBash().withScope(ConfigScope.WINDOWS),

    Alias('home').to(cdInto('~').withScope(ConfigScope.LAPTOP)),
    Alias('home').to('murexcli').withScope(ConfigScope.MUREX),
    Alias('src').to(cdInto(envSyncRepoPath)),
    Alias('desk').to(cdInto(DESKTOP)),
    Alias('downloads').to(cdInto(DOWNLOADS)),
    Alias('docs').to(cdInto(DOCUMENTS)),

    Alias('cdpaste').to(cdInto('"$(paste | aspath -linux)"')).withTag('Quick Navigation'),
    Alias('back').to('cd').addArg('..').andThen('ls').withTag('Quick Navigation'),
    Function('cdl').thenExecute([
        cdInto('"$1"').andThen('ls'),
        ]).withTag('Quick Navigation'),

    Alias('music').to(cdInto('D:\\Music')).withScope(ConfigScope.LAPTOP),
    Alias('pics').to(cdInto('D:\\Camera Roll')).withScope(ConfigScope.LAPTOP),
    Alias('vids').to(cdInto('D:\\Videos')).withScope(ConfigScope.LAPTOP),
    Alias('movies').to(cdInto('D:\\Videos\\Movies')).withScope(ConfigScope.LAPTOP),

    Alias('exp').to(RunPython(UTILS_PATH / 'exp.py')),
    Alias('start').to(RunPython(UTILS_PATH / 'start.py')),
    Alias('win').to(RunPython(UTILS_PATH / 'win.py')).withScope(ConfigScope.WINDOWS),
    Alias('netpass').to(RunPython(envSyncSrcPath / 'NetPass' / 'netpass.py')).withScope(ConfigScope.WINDOWS),

    Function('restart').thenExecute([
        Exec('win 2').disown(),
        Exec('exit'),
        ]).withTag('bash').withScope(ConfigScope.WINDOWS),

    Alias('reload').to('updatebashprofile').andThen('restart').withTag('bash').withScope(ConfigScope.WINDOWS),
    Alias('cat').to('bat').withTag('bash'),
    Alias(':r').to('restart').withTag('bash').withScope(ConfigScope.WINDOWS),
    Alias(':q').to('win 2').andThen('exit').withTag('bash').withScope(ConfigScope.WINDOWS),
    Alias('bashprofile').to('code').addPath(globalEnv.getBashProfilePath()).withTag('bash').withScope(ConfigScope.WINDOWS),

    Function('color').thenExecute([
        Exec('grep').addArg('--color').addArg('-E').addArg('"$1|^"'),
        ]).withTag('Grep color'),

    Function('col').thenExecute([
        Exec('awk').addArg('-v column="$1"').addArg("'{print $column}'"),
        ]).withTag('awk shortcut'),

    Alias('editvimrc').to('code').addPath(globalEnv.getVimrcPath()).withTag('Config'),
    Alias('editbashprofile').to('code').addPath(CURRENT_FILE).withTag('Config'),
    Alias('updatebashprofile').to(RunPython(CURRENT_FILE)).addArg('--in_place').withTag('Config'),
    Alias('updatevimrc').to(RunPython(envSyncSrcPath / 'config' / 'VimRC.py').addArg('--in_place')).withTag('Config'),

    Alias('cls').to('clear').then('jobs').withTag('OS'),
    Alias('cmd').to('start').addPath('C:\\Windows\\System32\\cmd.exe').withTag('OS').withScope(ConfigScope.WINDOWS),

    Alias('connected').to('curl -s www.google.com').muteOutput().withTag('OS'),
    Alias('checkConnection').to('connected').then('echo $?').withTag('OS'),

    Alias('size').to(RunPython(UTILS_PATH / 'size.py')).withTag('OS'),

    Alias('tm').to(InlinePython().linesAre([
        'import pyautogui',
        'pyautogui.hotkey("ctrl", "shift", "esc")'
    ])).withTag('Task Manager').withScope(ConfigScope.WINDOWS),

    Alias('vimpaste').to('paste').pipe('vim -').withTag('Vim'),
    Alias('pastevim').to('paste').pipe('vim -').withTag('Vim'),

    Alias('gs').to('git status').withTag('Git'),
    Alias('gd').to('git diff -w').withTag('Git'),
    Alias('gln').to('git log -n').withTag('Git'),

    Alias('updategitbash').to(updateGitBash).withTag('Update Git Bash').withScope(ConfigScope.WINDOWS),

    Alias('count').to('wc').addArg('-l').withTag('Quick count lines'),

    Alias('clip').to(copy).withTag('Clipboard'),
    Alias('paste').to(paste).pipe('tr -d').addArg(r'"\r"').withTag('Clipboard'),

    Exec('ps aux').grep('ssh-agent').pipe('awk').addArg("'{print $1}'").pipe('xargs -r kill').withTag('Start Git SSH').withComment('Kill existing ssh-agents, if any'),
    Exec('eval "$(ssh-agent -s)"').muteOutput(3).withTag('Start Git SSH').withComment('Start a new ssh-agent for this session'),

    RunPython(envSyncRepoPath / 'src' / 'GlobalEnv.py').muteOutput(3).addArg('--decrypt')\
        .andThen('ssh-add').addPath(envSyncRepoPath / 'encrypted' / 'github_key').muteOutput(3).withTag('Start Git SSH')\
            .ifFailed('echo -n SSH Failed. config.json might contain a bad passphrase'),

    cdInto(envSyncRepoPath).withComment('Set git remote to use SSH for EnvSync repo'),
    Exec('git remote set-url origin git@github.com:lebenebou/EnvSync.git'),

    *mxVersionManagementOptions(),
    *mxdevenvOptions(),
    *murexCliOptions(),
    *murexLinkShortcuts(),
    *murexWelcomeMessage(),

    Exec('echo Bashprofile simulation done.').withTag('Completion Message').onlyIfThroughScript(),

    ]

    if args.in_place:
        bashprofileContent: str = bashprofile.toString(scopeFilter=globalEnv.currentScope)
        ConfigFile.writeToFile(globalEnv.getBashProfilePath(), bashprofileContent)
    else:
        print(bashprofile.toString(), file=sys.stdout)

    exit(0)