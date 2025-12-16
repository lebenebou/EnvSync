
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
    Alias('debugme').to('mde envDebug -v $(version) -clientPath /d/apps/$(version)*').inParallel().withTag('DebugMe++'),

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
    ONEDRIVE_MUREX = (D_DRIVE / "OneDrive - Murex").withName('ONEDRIVE').withScope(ConfigScope.MUREX | ConfigScope.WINDOWS)
    murexSettingsJsonPath = os.path.join('D:\\', '.mxdevenvpp', 'settings', 'python_scripts_settings.json')

    murexSettings = dict()
    if GlobalEnv().currentScope & ConfigScope.MUREX:
        murexSettings = readJsonFromFile(murexSettingsJsonPath)

    CURRENT_VERSION = murexSettings.get('version', None)
    OLD_VERSION = murexSettings.get('previous_version', None)

    options: list[ConfigOption] = [

    # MxVersion
    Alias('version').to(f'echo {CURRENT_VERSION}').withTag('MxVersion'),
    Alias('clipVersion').to('version').tee('clip').withTag('MxVersion'),
    Alias('oldversion').to(f'echo {OLD_VERSION}').withTag('MxVersion'),

    # MxVersion manipulation
    Alias('cdversion').to(cdInto('/d/$(version)')).withTag('MxVersion Manipulation'),
    Alias('thorversion').to(cdInto('/d/$(latestThorVersion)')).withTag('MxVersion Manipulation'),
    Alias('cdapps').to(cdInto('/d/apps/$(version)*')).withTag('MxVersion Manipulation'),

    Alias('startversion').to('start').addArg('/d/$(version)/mx-$(version).sln.lnk').withTag('MxVersion Manipulation'),

    Alias('versionUpgrade').to(RunPython(ONEDRIVE_MUREX / 'Downloads' / 'scripts' / 'upgradeVersion.py')).withTag('MxVersion Manipulation'),

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
    Echo('Active version:').addArg('$(version)'),
    Exec('echo -e \n'),
    p4helperScript.addArg('--unmerged').withComment('Check for defects not yet in mainstream'),

    Exec('ls /u').muteOutput(3).ifFailed('echo "[WARNING]: Drives aren\'t mapped!"'),

    ]

    for option in options:

        if isinstance(option, Exec): option.onlyIfThroughGitBash()
        option.withScope(ConfigScope.MUREX)
        option.withTag('Welcome message')

    return options

def murexCliOptions() -> list[ConfigOption]:

    C_DRIVE = Path("C:\\").withName('C Drive').withScope(ConfigScope.WINDOWS)
    D_DRIVE = Path("D:\\").withName('D Drive').withScope(ConfigScope.WINDOWS)
    ONEDRIVE_MUREX = (D_DRIVE / "OneDrive - Murex").withName('ONEDRIVE').withScope(ConfigScope.MUREX | ConfigScope.WINDOWS)

    MUREX_CLI = (C_DRIVE / 'murexcli')

    # Murex scripts
    GQAF_SCRIPTS = (MUREX_CLI / 'gqaf')
    p4helperScript = RunPython(MUREX_CLI / 'p4helper.py')
    jenkinsScript = RunPython(MUREX_CLI / 'JenkinsRequestHandler.py')
    integrationScript = RunPython(MUREX_CLI / 'IntegrationRequestHandler.py')

    options: list[ConfigOption] = [

    Alias('home').to(cdInto(MUREX_CLI)),
    Alias('scripts').to(cdInto(ONEDRIVE_MUREX / 'Downloads' / 'scripts')),

    # Session info
    Alias('sessionInfo').to(RunPython(MUREX_CLI / 'SessionInfo.py')).withTag('Session Info'),

    Alias('displayAlien').to(RunPython(MUREX_CLI / 'display_alien' / 'excel_refresher.py')\
                             .andThen('start').addPath(MUREX_CLI / 'display_alien' / 'display_alien.xlsx')),

    # P4 Helpers
    Alias('p4helper').to(p4helperScript).withTag('P4 Helpers'),
    Alias('psubmit').to('p4helper').addArg('--submit').addArg('$(paste)').withTag('P4 Helpers'),
    Alias('submit').to('p4helper --submit').withTag('P4 Helpers'),
    Alias('isItMerged').to('echo "looking for $(paste)..."').andThen('p4helper --me --build').pipe('greppaste').withTag('P4 Helpers'),
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

    Alias('latestThorVersion').to('allMxVersions').grep('-E').addQuoted(r'mar.tho.[0-9]+\S+[0-9]$').pipe('sort -Vr').pipe('head -n 1').withTag('Thor Team'),

    ]

    for option in options:
        option.withScope(ConfigScope.MUREX)

    return options

def enableGitUntrackedCacheForMurexVersion() -> ConfigOption:

    cdIntoVersion = Exec('cdversion')
    enableCacheLocally = Exec('git config core.untrackedCache true')
    enableFsMonitor = Exec('git config core.fsmonitor true')

    return cdIntoVersion.andThen(enableCacheLocally).andThen(enableFsMonitor).withScope(ConfigScope.MUREX)

def batUtilityAliases() -> list[ConfigOption]:

    batFolder = Path(GlobalEnv().repoBinPath) / 'bat'
    zipFilePath = Path(GlobalEnv().repoBinPath) / 'bat.zip'

    checkBatInstalled = Exec(f'[ -f "{(batFolder / "bat.exe").toLinuxPath()}" ]')
    clearBatFolder = Exec('rm -rf').addPath(batFolder).addPath(batFolder)

    zipUrl: str = 'https://github.com/sharkdp/bat/releases/download/v0.26.1/bat-v0.26.1-x86_64-pc-windows-msvc.zip'

    downloadBatZip = Exec('curl -L').addArg(zipUrl).addArg('-o').addPath(zipFilePath).addArg('-s')
    unzipBat = Exec('unzip').addPath(zipFilePath).addArg('-d').addPath(GlobalEnv().repoBinPath).muteOutput(3)
    renameExtractedZip = Exec('mv').addPath(Path(GlobalEnv().repoBinPath) / 'bat-v0.26.1-x86_64-pc-windows-msvc').addPath(batFolder)

    updateBat = clearBatFolder.andThen(downloadBatZip).andThen(unzipBat).andThen(renameExtractedZip).andThen(Exec('rm').addPath(zipFilePath))

    options: list[ConfigOption] = [

        Alias('bat').to(batFolder / 'bat.exe'),
        Alias('cat').to('bat'),

        checkBatInstalled.ifFailed(Echo('bat not found, installing...').andThen(updateBat)),
        Alias('updatebat').to(updateBat),
    ]

    for option in options:
        option.withScope(ConfigScope.COMMON)
        option.withTag('bat Utility')

    return options

def jqUtilityAliases() -> list[ConfigOption]:

    jqLatestExeUrl = 'https://github.com/jqlang/jq/releases/latest/download/jq-win64.exe'
    jqExePath = Path(GlobalEnv().repoRootPath) / 'bin' / 'jq.exe'

    installLatestjq = Exec(f'curl -L {jqLatestExeUrl}').addArg('-o').addPath(jqExePath).addArg('-s')
    checkJqInstalled = Exec(f'[ -f "{jqExePath.toLinuxPath()}" ]')

    options: list[ConfigOption] = [

        Alias('updatejq').to(installLatestjq),
        Alias('jq').to(jqExePath),

        checkJqInstalled.ifFailed(Echo('jq not found, installing...').andThen(installLatestjq)),
    ]

    for option in options:
        option.withScope(ConfigScope.COMMON)
        option.withTag('jq Utility')

    return options

def usualShellAliases() -> list[ConfigOption]:

    options: list[ConfigOption] = [

    Alias('cls').to('clear').then('jobs').withComment('List running jobs when terminal is cleared'),

    # Git
    Alias('gs').to('git status').withTag('Git'),
    Alias('gd').to('git diff -w').withTag('Git'),
    Alias('gln').to('git log --oneline --pretty=format:"%h by %al - %s" -n').withTag('Git'),

    Alias('commit').to('git commit').withTag('Git'),
    Alias('commitFromClipBoard').to('git commit -m "$(paste)"').withTag('Git'),

    Function('commitFromJiraId').thenExecute([
        # save the commit message from jira id passed as argument 1
        Exec('description=$(jira --id $1)').ifFailed(Echo('Jira ID $1 not found!').andThen('return 1')),
        Exec('git commit -m "$description"'),
        ]).withTag('Git').withScope(ConfigScope.MUREX),

    Alias('amend').to('git commit --amend').withTag('Git'),
    Alias('push').to('git push').withTag('Git'),

    Alias('master').to('git switch master').withTag('Git'),
    Alias('main').to('git switch main').withTag('Git'),

    # Git Options
    Exec('git config --global core.untrackedCache false').withTag('Git Options'),

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

    # cat
    # Alias('cat').to('bat').withTag('bash').withScope(ConfigScope.WINDOWS),

    # vim
    Alias('vimpaste').to('paste').pipe('vim -').withTag('vim'),
    Alias('pastevim').to('paste').pipe('vim -').withTag('vim'),

    # wc
    Alias('count').to('wc').addArg('-l').withTag('wc'),

    # network
    Alias('connected').to('curl -s www.google.com').muteOutput().withTag('network'),
    Alias('checkConnection').to('connected').then('echo $?').withTag('network'),

    ]

    return options

def initSSH() -> list[ConfigOption]:

    killAllSshAgents = Exec('ps aux').grep('ssh-agent').pipe('awk').addArg("'{print $1}'").pipe('xargs -r kill')
    startNewSshAgent = Exec('eval "$(ssh-agent -s)"').muteOutput(3)

    attemptPrivateKeyDecryption = RunPython(Path(GlobalEnv().repoRootPath) / 'src' / 'GlobalEnv.py').muteOutput(3).addArg('--decrypt')
    printFailureMessage = Exec('echo -n SSH Failed. config.json might contain a bad passphrase')

    options: list[ConfigOption] = [

    killAllSshAgents,
    startNewSshAgent,

    attemptPrivateKeyDecryption\
        .andThen('ssh-add').addPath(Path(GlobalEnv().repoRootPath) / 'encrypted' / 'github_key').muteOutput(3).withTag('Start Git SSH')\
            .ifFailed(printFailureMessage),

    cdInto(GlobalEnv().repoRootPath).withComment('Set git remote to use SSH for EnvSync repo'),
    Exec('git remote set-url origin git@github.com:lebenebou/EnvSync.git'),

    ]

    for option in options:

        if isinstance(option, Exec):
            option.onlyIfThroughGitBash()

        option.withScope(ConfigScope.WINDOWS)
        option.withTag('Start Git SSH')

    return options


def maximizeAndZoomScreen() -> ConfigOption:

    pythonLinesToRun: list[str] = [
        'import pyautogui',
        'pyautogui.hotkey("win", "up")',
    ]

    zoomIterations = 3
    if GlobalEnv().currentScope & ConfigScope.LAPTOP:
        zoomIterations = 2

    for _ in range(zoomIterations):
        pythonLinesToRun.append('pyautogui.hotkey("ctrl", "+")')

    command: ConfigOption = InlinePython(runImmediately=True).linesAre(pythonLinesToRun).onlyIfThroughGitBash().withScope(ConfigScope.WINDOWS)
    return command

def navigationAliases() -> list[ConfigOption]:

    globalEnv = GlobalEnv()

    # Windows drives
    D_DRIVE = Path("D:\\").withName('D Drive').withScope(ConfigScope.WINDOWS)
    ONEDRIVE_MUREX = (D_DRIVE / "OneDrive - Murex").withName('ONEDRIVE').withScope(ConfigScope.MUREX | ConfigScope.WINDOWS)

    # User folders
    DESKTOP = Path(os.path.join(globalEnv.userHomeDir, 'Desktop')).withName('DESKTOP').withScope(ConfigScope.LAPTOP | ConfigScope.LINUX)
    DOWNLOADS = Path(os.path.join(globalEnv.userHomeDir, 'Downloads')).withName('DOWNLOADS').withScope(ConfigScope.LAPTOP)
    DOCUMENTS = Path('C:\\Users\\yyamm\\Documents\\MyDocuments').withName('DOCUMENTS').withScope(ConfigScope.LAPTOP)

    if globalEnv.currentScope & ConfigScope.MUREX:

        DESKTOP = (ONEDRIVE_MUREX / 'Desktop').withScope(ConfigScope.MUREX)
        DOWNLOADS = (ONEDRIVE_MUREX / 'Downloads').withScope(ConfigScope.MUREX)
        DOCUMENTS = (ONEDRIVE_MUREX / 'Documents').withScope(ConfigScope.MUREX)

    if globalEnv.currentScope & ConfigScope.LINUX:
        DOCUMENTS = Path(os.path.join(globalEnv.userHomeDir, 'Documents')).withName('DOCUMENTS').withScope(ConfigScope.LINUX)
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

    Alias('restart').to('win 2').disown().then('exit').withTag('bash').withScope(ConfigScope.WINDOWS),

    Alias(':r').to('restart').withTag('bash').withScope(ConfigScope.WINDOWS),
    Alias(':q').to('exit').withTag('bash').withScope(ConfigScope.WINDOWS),

    ]

    return options

def vsCodeAliases() -> list[ConfigOption]:

    killVsCode = Exec('tasklist').grep('-i ^code.exe').pipe('col 2').pipe('xargs -n1 -r taskkill //PID').muteOutput(2)

    options: list[ConfigOption] = [

    Alias('vscode').to(killVsCode).then('code'),

    ]

    for option in options:
        option.withTag('VS Code')

    return options

def configAliases() -> list[ConfigOption]:

    globalEnv = GlobalEnv()
    envSyncSrcPath = Path(globalEnv.repoSrcPath)

    options: list[ConfigOption] = [

    # BashProfile config
    Alias('bashprofile').to('code').addPath(globalEnv.getBashProfilePath()).withScope(ConfigScope.WINDOWS).withTag('BashProfile Config'),
    Alias('editbashprofile').to('code').addPath(CURRENT_FILE).withTag('BashProfile Config'),
    Alias('refresh').to(RunPython(CURRENT_FILE)).addArg('--in_place').withTag('BashProfile Config'),

    # VimRC config
    Alias('editvimrc').to('code').addPath(globalEnv.getVimrcPath()).withTag('VimRC Config'),
    Alias('updatevimrc').to(RunPython(envSyncSrcPath / 'config' / 'VimRC.py').addArg('--in_place')).withTag('VimRC Config'),

    ]

    return options

def envSyncAliases() -> list[ConfigOption]:

    globalEnv = GlobalEnv()
    envSyncSrcPath = Path(globalEnv.repoSrcPath).withName('SRC PATH')
    utilsPath = (envSyncSrcPath / 'utils').withName('UTILS PATH')

    options: list[ConfigOption] = [

    # EnvSync utils
    Alias('aspath').to(RunPython(utilsPath / 'aspath.py').addArg('--from_stdin')).withTag('EnvSync utils'),
    Alias('exp').to(RunPython(utilsPath / 'exp.py')).withTag('EnvSync utils'),
    Alias('start').to(RunPython(utilsPath / 'start.py')).withTag('EnvSync utils'),
    Alias('win').to(RunPython(utilsPath / 'win.py')).withScope(ConfigScope.WINDOWS).withTag('EnvSync utils'),
    Alias('size').to(RunPython(utilsPath / 'size.py')).withTag('EnvSync utils'),
    Alias('netpass').to(RunPython(envSyncSrcPath / 'NetPass' / 'netpass.py')).withScope(ConfigScope.WINDOWS).withTag('EnvSync utils'),

    # EnvSync clipboard
    Alias('clip').to(RunPython(utilsPath / 'clipboard.py').addArg('--copy')).withTag('EnvSync clipboard'),
    Alias('paste').to(RunPython(utilsPath / 'clipboard.py').addArg('--paste')).pipe('tr -d').addArg(r'"\r"').withTag('EnvSync clipboard'),

    # EnvSync personal
    Alias('money').to(RunPython(envSyncSrcPath / 'finance' / 'main.py')).withTag('EnvSync personal'),

    ]

    return options

def windowsAliases() -> list[ConfigOption]:

    options: list[ConfigOption] = [

    Alias('tm').to(InlinePython().linesAre([
        'import pyautogui',
        'pyautogui.hotkey("ctrl", "shift", "esc")'
    ])).withTag('Windows Task Manager'),

    Alias('cmd').to('start').addPath('C:\\Windows\\System32\\cmd.exe').withTag('Windows CMD'),

    Alias('path').to(Echo('$PATH')).pipe('tr').addArg('":"').addArg(r'"\n"').withTag('Windows PATH'),

    ]

    for option in options:
        option.withScope(ConfigScope.WINDOWS)

    return options

if __name__ == "__main__":

    # parse args
    parser = argparse.ArgumentParser(description='Update your bashprofile through Python')

    optionGroup = parser.add_mutually_exclusive_group()
    optionGroup.add_argument('-i', '--in_place', action='store_true', help='Directly modify ~/.bash_profile')

    args = parser.parse_args()

    bashprofile: ConfigFile = BashProfile()
    bashprofile.options = [

    maximizeAndZoomScreen(),
    Exec('mkdir -p').addPath(Path(GlobalEnv().repoRootPath) / 'bin').withComment('Ensure bin directory exists'),

    *usualShellAliases(),
    *navigationAliases(),
    *gitBashManipulationAliases(),

    *envSyncAliases(),
    *configAliases(),
    *vsCodeAliases(),

    *windowsAliases(),
    *jqUtilityAliases(),
    *batUtilityAliases(),

    Alias('theplan').to('start').addPath(os.path.join('G:\\', 'My Drive', 'THE_PLAN.xlsx')).withScope(ConfigScope.WINDOWS).withTag('Personal Files'),

    *mxVersionManagementOptions(),
    *mxdevenvOptions(),

    *murexLinkShortcuts(),

    *murexCliOptions(),
    *murexWelcomeMessage(),
    # enableGitUntrackedCacheForMurexVersion(),

    *initSSH(),

    cdInto(GlobalEnv().repoRootPath).withComment('Set EnvSync repo as starting directory').withTag('Starting Directory'),

    Echo('Bashprofile simulation done.').withTag('Completion Message').onlyIfThroughScript(),

    ]

    assert all(isinstance(option, ConfigOption) for option in bashprofile.options), "All items in bashprofile.options must be of type ConfigOption"

    globalEnv = GlobalEnv()

    if args.in_place:
        bashprofileContent: str = bashprofile.toString(scopeFilter=globalEnv.currentScope)
        ConfigFile.writeToFile(globalEnv.getBashProfilePath(), bashprofileContent)
    else:
        print(bashprofile.toString(), file=sys.stdout)

    exit(0)