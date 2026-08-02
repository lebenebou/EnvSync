
import sys, os
import argparse

CURRENT_FILE = os.path.abspath(__file__)
CONFIG_DIR = os.path.dirname(CURRENT_FILE)
SRC_DIR = os.path.dirname(CONFIG_DIR)
sys.path.append(SRC_DIR)

from GlobalEnv import GlobalEnv, ConfigScope
from config.Aliases import *

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
    Alias('debugme').to('mde envDebug -v $(version) -clientPath /d/apps/$(version)*').inParallel().withTag('DebugMe++'),

    # drive mapping
    Alias('drivesmapped').to('[ -d "/u" ]').then(Echo('$?')).withTag('Drive Mapping'),
    Alias('unmapdrives').to('start').addPath(os.path.join(mxdevenvUtilityScriptsPath, 'mapsremove.bat')).withTag('Drive Mapping'),
    Alias('mapdrives').to('unmapdrives').delay(1).andThen('start').addPath(os.path.join(mxdevenvUtilityScriptsPath, 'mapsFR.vbs')).delay(0.5).andThen('ls /u').withTag('Drive Mapping'),

    ]

    for option in options:
        option.withScope(ConfigScope.MUREX)

    return options

def mxVersionManagementOptions() -> list[ConfigOption]:

    D_DRIVE = Path("D:\\")
    ONEDRIVE_MUREX = (D_DRIVE / "OneDrive - Murex").withScope(ConfigScope.MUREX | ConfigScope.WINDOWS)
    murexSettingsJsonPath = os.path.join('D:\\', '.mxdevenvpp', 'settings', 'python_scripts_settings.json')

    murexSettings = dict()
    if GlobalEnv().isInScope(ConfigScope.MUREX):
        murexSettings = readJsonFromFile(murexSettingsJsonPath)

    CURRENT_VERSION = murexSettings.get('version', None)
    OLD_VERSION = murexSettings.get('previous_version', None)

    vfind = Exec('cdversion').andThen('find').addArg('-t f')

    for ext in ['obj', 'pdb', 'ipch', 'user']:
        vfind.addArg('--exclude').addArg(f'*.{ext}')

    options: list[ConfigOption] = [

    Alias('version').to(Echo(CURRENT_VERSION)),
    Alias('clipVersion').to('version').tee('clip'),
    Alias('oldversion').to(Echo(OLD_VERSION)),

    Alias('cdversion').to(cdInto('/d/$(version)')),
    Alias('cdapps').to(cdInto('/d/apps/$(version)*')),

    Alias('startversion').to('start').addArg('/d/$(version)/mx-$(version).sln.lnk'),

    Alias('versionUpgrade').to(RunPython(ONEDRIVE_MUREX / 'Downloads' / 'scripts' / 'upgradeVersion.py'))\
        .andThen(Alias('version').to(Echo('$(paste)'))),

    Alias('settings').to('vim').addPath(murexSettingsJsonPath),

    Alias('vfind').to(vfind),

    ]

    for option in options:
        option.withScope(ConfigScope.MUREX)
        option.withTag('MxVersion')

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

    Echo('Active version:').addArg('$(version)'),
    Echo('-e \n'),
    p4helperScript.addArg('--unmerged').withComment('Check for defects not yet in mainstream'),

    Exec('ls /u').muteOutput(),
    IfPreviousFailed(EchoWarning('Drives are not mapped!')).Else(EchoSuccess('Drives mapped')),

    ]

    for option in options:

        if isinstance(option, Exec): option.onlyIfThroughGitBash()
        option.withScope(ConfigScope.MUREX)
        option.withTag('Welcome message')

    return options

def murexCliOptions() -> list[ConfigOption]:

    C_DRIVE = Path("C:\\").withScope(ConfigScope.WINDOWS)
    D_DRIVE = Path("D:\\").withScope(ConfigScope.WINDOWS)
    ONEDRIVE_MUREX = (D_DRIVE / "OneDrive - Murex").withScope(ConfigScope.MUREX | ConfigScope.WINDOWS)

    MUREX_CLI = (C_DRIVE / 'murexcli')

    # Murex scripts
    GQAF_SCRIPTS = (MUREX_CLI / 'gqaf')
    p4helperScript = RunPython(MUREX_CLI / 'p4helper.py')
    jenkinsScript = RunPython(MUREX_CLI / 'JenkinsRequestHandler.py')
    integrationScript = RunPython(MUREX_CLI / 'IntegrationRequestHandler.py')
    wikiScript = RunPython(MUREX_CLI / 'WikiPageRequestHandler.py')

    options: list[ConfigOption] = [

    Alias('home').to(cdInto(MUREX_CLI)),
    Alias('scripts').to(cdInto(ONEDRIVE_MUREX / 'Downloads' / 'scripts')),

    # Session info
    Alias('sessionInfo').to(RunPython(MUREX_CLI / 'SessionInfo.py')).withTag('Session Info'),

    Alias('displayAlien').to(RunPython(MUREX_CLI / 'display_alien' / 'excel_refresher.py')\
                             .andThen('start').addPath(MUREX_CLI / 'display_alien' / 'display_alien.xlsx')),

    # Wiki Helpers
    Alias('wikitext').to(wikiScript).addArg('--pageLink').addArg('"$(paste)"').withTag('Wiki Helpers'),

    # P4 Helpers
    Alias('p4helper').to(p4helperScript).withTag('P4 Helpers'),
    Alias('psubmit').to('p4helper').addArg('--submit').addArg('"$(paste)"').withTag('P4 Helpers'),
    Alias('submit').to('p4helper --submit').withTag('P4 Helpers'),
    Alias('isItMerged').to(Echo('looking for $(paste)...')).andThen('p4helper --me --build').pipe('greppaste').withTag('P4 Helpers'),
    Alias('dtk').to('start').addPath('D:\\tools\\dtk\\tk.3.rc.1\\toolkit.bat').withTag('P4 Helpers'),

    # Jira
    Alias('jira').to(RunPython(MUREX_CLI / 'JiraRequestHandler.py')).withTag('Jira Helpers'),

    # Jenkins
    Alias('jenkins').to(jenkinsScript).withTag('Jenkins Helpers'),
    Alias('integrate').to(integrationScript).withTag('Jenkins Helpers'),

    # Personal scripts
    Alias('mxOpen').to(RunPython(ONEDRIVE_MUREX / 'Downloads' / 'scripts' / 'mxOpen.py')).withTag('Personal Scripts'),
    Alias('coco').to(RunPython(ONEDRIVE_MUREX / 'Downloads' / 'scripts' / 'mxOpen.py')).addArg('--coconut').withTag('Personal Scripts'),
    Alias('auth').to(RunPython(ONEDRIVE_MUREX / 'Downloads' / 'scripts' / 'auth.py')).withTag('Personal Scripts'),

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

def gitEnableCacheForLargeRepo() -> Exec:

    enableCacheLocally = Exec('git config core.untrackedCache true')
    enableFsMonitor = Exec('git config core.fsmonitor true')

    return enableCacheLocally.andThen(enableFsMonitor).withScope(ConfigScope.MUREX)

def enableGitCacheForMurexVersion() -> Exec:

    cdVersion = cdInto('/d/$(version)')
    return cdVersion.andThen(gitEnableCacheForLargeRepo()).withScope(ConfigScope.MUREX)

def gitAliases() -> list[ConfigOption]:

    commitCount: int = 3
    improvedGitStatus = Exec('git status').\
                                andThen(Echo(rf'-e "\nLast {commitCount}" commits:'))\
                                .andThen(f'gln {commitCount}')

    gitOptions: list[ConfigOption] = [

    Alias('gs').to(improvedGitStatus),
    Alias('gd').to('git diff -w'),
    Alias('gln').to('git log --oneline --pretty=format:"%h by %al - %s" -n'),

    # git enable cache for large repo
    Alias('gitEnableCacheForLargeRepo').to(gitEnableCacheForLargeRepo()),

    # commit
    Alias('commit').to('git commit'),
    Alias('commitFromClipBoard').to('git commit -m "$(paste)"'),
    Alias('jiraCommit').to('git commit -m "$(jira --id $(paste))"').withScope(ConfigScope.MUREX),
    Alias('amend').to('git commit --amend'),

    # push
    Alias('push').to('git push'),

    # branch
    Alias('master').to('git switch master'),

    # Git Options
    Exec('git config --global core.untrackedCache false'),

    ]

    for i in range(1, 11):
        # Example: gd1 => git diff head~1 head
        gdnAlias = Alias(f'gd{i}').to(f'git diff head~{i} head')
        gitOptions.append(gdnAlias)

    for op in gitOptions:
        op.withTag('Git')

    return gitOptions
def usualShellAliases() -> list[ConfigOption]:

    options: list[ConfigOption] = [

    Alias('cls').to('clear').then('jobs').withComment('List running jobs when terminal is cleared'),

    # grep
    Alias('grep').to('grep -i --color --binary-files=without-match --exclude-dir=".git"').withTag('grep'),
    Alias('greppaste').to('grep').addArg('"$(paste)"').withTag('grep'),
    Alias('grepdefects').to('grep -Eo').addQuoted('DEF[0-9]+').withTag('grep').withScope(ConfigScope.MUREX),

    Function('color').thenExecute([
        Exec('grep').addArg('--color').addArg('-E').addArg('"$1|^"'),
        ]).withTag('grep'),

    # awk
    Function('col').thenExecute([
        Exec('awk').addArg('-v column="$1"').addArg("'{print $column}'"),
        ]).withTag('awk'),

    # vim
    Alias('vimpaste').to('paste').pipe('vim -').withTag('vim'),
    Alias('pastevim').to('paste').pipe('vim -').withTag('vim'),

    # wc
    Alias('count').to('wc').addArg('-l').withTag('wc'),

    # network
    Alias('connected').to('curl -s www.google.com').muteOutput().withTag('network'),
    Alias('checkConnection').to('connected').then(Echo('$?')).withTag('network'),

    Alias('unzip').to(Script('unzip_to_dir.sh')),

    ]

    return options


def maximizeAndZoomScreen() -> ConfigOption:

    pythonLinesToRun: list[str] = [
        'import pyautogui',
        'pyautogui.press("alt")',
        'pyautogui.press("space")',
        'pyautogui.press("r")',
        'pyautogui.hotkey("win", "up")',
        'pyautogui.hotkey("ctrl", "0")',
    ]

    zoomIterations = 3
    if GlobalEnv().isInScope(ConfigScope.LAPTOP):
        zoomIterations = 2

    for _ in range(zoomIterations):
        pythonLinesToRun.append('pyautogui.hotkey("ctrl", "+")')

    command: ConfigOption = InlinePython(runImmediately=True).linesAre(pythonLinesToRun).onlyIfThroughGitBash().withScope(ConfigScope.WINDOWS)
    return command

def navigationAliases() -> list[ConfigOption]:

    globalEnv = GlobalEnv()

    # Windows drives
    D_DRIVE = Path("D:\\").withScope(ConfigScope.WINDOWS)
    ONEDRIVE_MUREX = (D_DRIVE / "OneDrive - Murex").withScope(ConfigScope.MUREX | ConfigScope.WINDOWS)

    # User folders
    DESKTOP = Path(os.path.join(globalEnv.userHomeDir, 'Desktop')).withScope(ConfigScope.LAPTOP | ConfigScope.LINUX)
    DOWNLOADS = Path(os.path.join(globalEnv.userHomeDir, 'Downloads')).withScope(ConfigScope.LAPTOP)
    DOCUMENTS = Path('C:\\Users\\yyamm\\Documents\\MyDocuments').withScope(ConfigScope.LAPTOP)

    if globalEnv.isInScope(ConfigScope.MUREX):

        DESKTOP = (ONEDRIVE_MUREX / 'Desktop').withScope(ConfigScope.MUREX)
        DOWNLOADS = (ONEDRIVE_MUREX / 'Downloads').withScope(ConfigScope.MUREX)
        DOCUMENTS = (ONEDRIVE_MUREX / 'Documents').withScope(ConfigScope.MUREX)

    if globalEnv.isInScope(ConfigScope.LINUX):
        DOCUMENTS = Path(os.path.join(globalEnv.userHomeDir, 'Documents')).withScope(ConfigScope.LINUX)
    options: list[ConfigOption] = [

    # Usual directories
    Alias('home').to(cdInto('~')).withScope(ConfigScope.LAPTOP).withTag('Directory Jumps'),
    Alias('src').to(cdInto(GlobalEnv().repoRootPath)).withTag('Directory Jumps'),
    Alias('desk').to(cdInto(DESKTOP)).withTag('Directory Jumps'),
    Alias('downloads').to(cdInto(DOWNLOADS)).withTag('Directory Jumps'),
    Alias('docs').to(cdInto(DOCUMENTS)).withTag('Directory Jumps'),

    # Quick navigation
    Alias('cdpaste').to(cdInto('"$(paste | aspath -linux)"')).withTag('Relative Navigation'),

    Function('cdl').thenExecute([
        cdInto('"$1"').andThen('ls'),
        ]).withTag('Relative Navigation'),

    Alias('back').to('cd').addArg('..').andThen('ls').withTag('Relative Navigation'),

    # Media directories
    Alias('music').to(cdInto('D:\\Music')).withScope(ConfigScope.LAPTOP).withTag('Media Directories'),
    Alias('pics').to(cdInto('D:\\Camera Roll')).withScope(ConfigScope.LAPTOP).withTag('Media Directories'),
    Alias('vids').to(cdInto('D:\\Videos')).withScope(ConfigScope.LAPTOP).withTag('Media Directories'),
    Alias('movies').to(cdInto('D:\\Videos\\Movies')).withScope(ConfigScope.LAPTOP).withTag('Media Directories'),

    ]

    return options

def gitBashManipulationAliases() -> list[ConfigOption]:

    options: list[ConfigOption] = [

    Alias('updategitbash').to('git update-git-for-windows').withScope(ConfigScope.WINDOWS).withTag('Git-Bash Update'),

    Alias('runbashprofile').to(RunPython(CURRENT_FILE)).withTag('bashprofile'),
    Alias('editbashprofile').to('code').addPath(CURRENT_FILE).withTag('bashprofile'),

    Alias('restart').to('win 2').disown().then('exit').withTag('bash').withScope(ConfigScope.WINDOWS),

    Alias(':r').to('restart').withTag('bash').withScope(ConfigScope.WINDOWS),
    Alias(':q').to('exit').withTag('bash').withScope(ConfigScope.WINDOWS),

    ]

    return options

def aliasBinUtilities() -> list[ConfigOption]:

    options: list[ConfigOption] = []

    if not os.path.isdir(GlobalEnv().repoBinPath):
        return options

    for root, dirs, files in os.walk(GlobalEnv().repoBinPath):
        for file in files:

            if not file.endswith('.exe'):
                continue

            utilityBaseName = os.path.splitext(file)[0]
            options.append(
                Alias(utilityBaseName).to(os.path.join(root, file))
            )

            continue

        continue

    # custom options
    options.extend([
        Alias('find').to('fd').addArg('--no-ignore').addArg('--ignore-case').addArg('--hidden').addArg('--exclude .git'),
        Alias('cat').to('bat')
    ])

    for option in options:
        option.withTag('Bin Utilities')

    return options

def envSyncAliases() -> list[ConfigOption]:

    globalEnv = GlobalEnv()
    envSyncSrcPath = Path(globalEnv.repoSrcPath)
    utilsPath = (envSyncSrcPath / 'utils')

    debugMode: bool = bool(0)
    options: list[ConfigOption] = [] if debugMode else [

    # EnvSync main
    Alias('init').to(initScript()).withTag('EnvSync main'),
    Alias('config').to('init --config').withTag('EnvSync main'),
    Alias('reset').to(Script(os.path.join(globalEnv.repoRootPath, 'reset.sh'))).withTag('EnvSync main'),

    # EnvSync utils
    Alias('aspath').to(RunPython(utilsPath / 'aspath.py').addArg('--from_stdin')).withTag('EnvSync utils'),
    Alias('exp').to(RunPython(utilsPath / 'exp.py')).withTag('EnvSync utils'),
    Alias('start').to(RunPython(utilsPath / 'start.py')).withTag('EnvSync utils'),
    Alias('win').to(RunPython(utilsPath / 'win.py')).withScope(ConfigScope.WINDOWS).withTag('EnvSync utils'),
    Alias('size').to(RunPython(utilsPath / 'size.py')).withTag('EnvSync utils'),

    # EnvSync clipboard
    Alias('clip').to(RunPython(utilsPath / 'clipboard.py').addArg('--copy')).withTag('EnvSync clipboard'),
    Alias('paste').to(RunPython(utilsPath / 'clipboard.py').addArg('--paste')).pipe('tr -d').addArg(r'"\r"').withTag('EnvSync clipboard'),

    # EnvSync personal
    Alias('money').to(RunPython(envSyncSrcPath / 'finance' / 'main.py')).withTag('EnvSync personal'),
    Alias('theplan').to('start').addPath(os.path.join('G:\\', 'My Drive', 'THE_PLAN.xlsx')).withScope(ConfigScope.WINDOWS).withTag('EnvSync personal'),

    ]

    generateBashProfile = RunPython(CURRENT_FILE).muteOutput(2)
    checkDiff = Exec('diff -Bwq').addPath(globalEnv.getBashProfilePath()).addArg(f'<({generateBashProfile.toString()})')

    bashProfileCompareOptions: list[ConfigOption] = [

        Alias('checkbashprofile').to(checkDiff).andThen(Echo('$?')).withTag('BashProfile Check'),
        Echo(r'-ne Checking bashprofile...\\r'),
        checkDiff.muteOutput(),

        IfPreviousSucceeded(EchoSuccess('Bashprofile up to date'))\
            .Else(EchoWarning('Bashprofile might be outdated. Consider running init.sh --config')),

    ]

    for option in bashProfileCompareOptions:
        option.withTag('BashProfile Check')

    return bashProfileCompareOptions + options

def visualStudioAliases() -> list[ConfigOption]:

    options: list[ConfigOption] = [

    # vs command to open a file with vs
    Alias('vs').to(Script('vs.sh')),

    ]

    for option in options:
        option.withScope(ConfigScope.MUREX)
        option.withTag('Visual Studio')

    return options

def windowsAliases() -> list[ConfigOption]:

    options: list[ConfigOption] = [

    Alias('cmd').to('start').addPath('C:\\Windows\\System32\\cmd.exe').withTag('Windows CMD'),

    Alias('path').to(Echo('$PATH')).pipe('tr').addArg('":"').addArg(r'"\n"').withTag('Windows PATH'),

    ]

    for option in options:
        option.withScope(ConfigScope.WINDOWS)

    return options

def initScript() -> ConfigOption:

    initScriptPath = os.path.join(GlobalEnv().repoRootPath, 'init.sh')
    return Script(initScriptPath).toExecute()

if __name__ == "__main__":

    debugMode: bool = bool(0)

    # parse args
    parser = argparse.ArgumentParser(description='Update your bashprofile through Python')

    optionGroup = parser.add_mutually_exclusive_group()
    optionGroup.add_argument('-i', '--in_place', action='store_true', help='Directly modify ~/.bash_profile')

    args = parser.parse_args()

    bashprofile: ConfigFile = BashProfile()
    bashprofile.options = [] if debugMode else [

    maximizeAndZoomScreen(),
    Alias('python').to('py').withTag('Python').withScope(ConfigScope.LAPTOP),
    initScript(),

    *gitAliases(),
    *usualShellAliases(),
    *navigationAliases(),
    *gitBashManipulationAliases(),
    *aliasBinUtilities(),

    *envSyncAliases(),

    *visualStudioAliases(),
    *windowsAliases(),

    *mxVersionManagementOptions(),
    *mxdevenvOptions(),

    *murexLinkShortcuts(),

    *murexCliOptions(),
    *murexWelcomeMessage(),
    enableGitCacheForMurexVersion(),

    cdInto(GlobalEnv().repoRootPath).withComment('Set EnvSync repo as starting directory').withTag('Starting Directory'),

    EchoSuccess('Bashprofile simulation done.').withTag('Completion Message').onlyIfThroughScript(),

    ]

    if debugMode:
        bashprofile.options = [
            Alias('init').to(initScript()).withTag('EnvSync main')
        ]

    assert all(isinstance(option, ConfigOption) for option in bashprofile.options), "All items in bashprofile.options must be of type ConfigOption"

    globalEnv = GlobalEnv()

    if args.in_place:
        bashprofileContent: str = bashprofile.toString(scopeFilter=globalEnv.currentScope)
        ConfigFile.writeToFile(globalEnv.getBashProfilePath(), bashprofileContent)
    else:
        print(bashprofile.toString(), file=sys.stdout)

    if debugMode:
        exit(1)

    exit(0)
