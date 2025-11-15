
import os
import sys
import argparse

from GlobalEnv import GlobalEnv, ConfigScope
from config.Aliases import *

CURRENT_FILE = os.path.abspath(__file__)

import json
def readJsonFromFile(filePath: str) -> dict:
    with open(filePath, 'r') as file:
        return json.load(file)

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
    ONEDRIVE_MUREX = D_DRIVE.slash("OneDrive - Murex").withName('ONEDRIVE').withScope(ConfigScope.MUREX | ConfigScope.WINDOWS)

    # Repo paths
    REPO_ROOT = Path(globalEnv.repoRootPath).withName('REPO ROOT PATH')
    SRC_PATH = Path(globalEnv.repoSrcPath).withName('SRC PATH')
    UTILS_PATH = SRC_PATH.slash('utils').withName('UTILS PATH')

    DESKTOP = Path(os.path.join(globalEnv.userHomeDir, 'Desktop')).withName('DESKTOP').withScope(ConfigScope.LAPTOP | ConfigScope.LINUX)\
        .withAlternateValueForScope(ConfigScope.MUREX, ONEDRIVE_MUREX.slash('Desktop'))

    DOWNLOADS = Path(os.path.join(globalEnv.userHomeDir, 'Downloads')).withName('DOWNLOADS').withScope(ConfigScope.LAPTOP)\
        .withAlternateValueForScope(ConfigScope.MUREX, ONEDRIVE_MUREX.slash('Downloads'))

    DOCUMENTS = Path('C:\\Users\\yyamm\\Documents\\MyDocuments').withName('DOCUMENTS').withScope(ConfigScope.LAPTOP)\
        .withAlternateValueForScope(ConfigScope.MUREX, os.path.join(globalEnv.gPavilion15Path, 'MyDocuments'))\
        .withAlternateValueForScope(ConfigScope.LINUX, os.path.join(globalEnv.userHomeDir, 'Documents'))

    MUREX_CLI = C_DRIVE.slash('murexcli').withScope(ConfigScope.MUREX)
    MUREX_SETTINGS_JSON = D_DRIVE.slash('.mxdevenvpp').slash('settings').slash('python_scripts_settings.json').withScope(ConfigScope.MUREX)

    murexSettings = dict()
    if globalEnv.currentScope & ConfigScope.MUREX:
        murexSettings = readJsonFromFile(MUREX_SETTINGS_JSON.value)

    MUREX_SETTINGS_PY = MUREX_CLI.slash('settings.py').withScope(ConfigScope.MUREX)
    U_MXDEVENV = Path('U:\\tools\\mxdevenv\\mxdevenvpp').withScope(ConfigScope.MUREX)
    D_MXDEVENV = Path('D:\\.mxdevenvpp').withScope(ConfigScope.MUREX)
    REPO_MXDEVENV = Path('C:\\mxdevenv').withScope(ConfigScope.MUREX)

    UNMAP_DRIVES_SCRIPT = REPO_MXDEVENV.slash('Mxdevenvpp').slash('_Scripts').slash('mapsremove.bat').withScope(ConfigScope.MUREX)
    MAP_DRIVES_SCRIPT = REPO_MXDEVENV.slash('Mxdevenvpp').slash('_Scripts').slash('mapsFR.vbs').withScope(ConfigScope.MUREX)

    USERNAME = murexSettings.get('username', globalEnv.hostname)
    PASSWORD = murexSettings.get('password', None)

    CURRENT_VERSION = murexSettings.get('version', None)
    OLD_VERSION = murexSettings.get('previous_version', None)

    updateGitBashCommand = Exec('git').addArg('update-git-for-windows').withScope(ConfigScope.WINDOWS)

    # Murex scripts
    GQAF_SCRIPTS = MUREX_CLI.slash('gqaf').withScope(ConfigScope.MUREX)
    p4helperScript = RunPython(MUREX_CLI.slash('p4helper.py')).withScope(ConfigScope.MUREX)
    jiraScript = RunPython(MUREX_CLI.slash('JiraRequestHandler.py')).withScope(ConfigScope.MUREX)
    jenkinsScript = RunPython(MUREX_CLI.slash('JenkinsRequestHandler.py')).withScope(ConfigScope.MUREX)
    integrationScript = RunPython(MUREX_CLI.slash('IntegrationRequestHandler.py')).withScope(ConfigScope.MUREX)

    # clipboard utilities
    copy = RunPython(UTILS_PATH.slash('clipboard.py')).addArg('--copy').withTag('Clipboard Utility')
    paste = RunPython(UTILS_PATH.slash('clipboard.py')).addArg('--paste').withTag('Clipboard Utility')

    # Main script
    runUnitTests()

    bashprofile: ConfigFile = BashProfile()
    bashprofile.options = [

    Alias('aspath').to(RunPython(UTILS_PATH.slash('aspath.py')).addArg('--from_stdin')).withTag(None),

    Alias('theplan').to('start').addPath(G_DRIVE.slash('My Drive').slash('THE_PLAN.xlsx')).withScope(ConfigScope.WINDOWS).withTag('Personal'),
    Alias('money').to(RunPython(SRC_PATH.slash('finance').slash('main.py'))).withTag('Personal'),

    Alias('grep').to('grep -i --color --binary-files=without-match --exclude-dir=".git"').withTag('Grep Options'),
    Alias('greppaste').to('grep').addArg('"$(paste)"').withTag('Grep Options'),
    Alias('gp').to('greppaste').withTag('Grep Options'),
    Alias('grepdefects').to('grep').addArg('-Eo').addQuoted('DEF[0-9]+').withTag('Grep Options').withScope(ConfigScope.MUREX),

    InlinePython(runImmediately=True).linesAre([
        'import pyautogui',
        'pyautogui.hotkey("win", "up")',
        'pyautogui.hotkey("ctrl", "+")',
        'pyautogui.hotkey("ctrl", "+")',
        'pyautogui.hotkey("ctrl", "+")',
    ]).withScope(ConfigScope.WINDOWS),

    Alias('home').to(cdInto('~').withScope(ConfigScope.LAPTOP)),
    Alias('home').to('murexcli').withScope(ConfigScope.MUREX),
    Alias('src').to(cdInto(REPO_ROOT)),
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

    Alias('exp').to(RunPython(UTILS_PATH.slash('exp.py'))),
    Alias('start').to(RunPython(UTILS_PATH.slash('start.py'))),
    Alias('win').to(RunPython(UTILS_PATH.slash('win.py'))).withScope(ConfigScope.WINDOWS),
    Alias('netpass').to(RunPython(SRC_PATH.slash('NetPass').slash('netpass.py'))).withScope(ConfigScope.WINDOWS),

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
    Alias('updatevimrc').to(RunPython(SRC_PATH.slash('config').slash('VimRC.py')).addArg('--in_place')).withTag('Config'),

    Alias('cls').to('clear').then('jobs').withTag('OS'),
    Alias('cmd').to('start').addPath('C:\\Windows\\System32\\cmd.exe').withTag('OS').withScope(ConfigScope.WINDOWS),

    Alias('connected').to('curl -s www.google.com').muteOutput().withTag('OS'),
    Alias('checkConnection').to('connected').then('echo $?').withTag('OS'),

    Alias('size').to(RunPython(UTILS_PATH.slash('size.py'))).withTag('OS'),

    Alias('tm').to(InlinePython().linesAre([
        'import pyautogui',
        'pyautogui.hotkey("ctrl", "shift", "esc")'
    ])).withTag('Task Manager').withScope(ConfigScope.WINDOWS),

    Alias('vimpaste').to('paste').pipe('vim -').withTag('Vim'),
    Alias('pastevim').to('paste').pipe('vim -').withTag('Vim'),

    Alias('gs').to('git status').withTag('Git'),
    Alias('gd').to('git diff -w').withTag('Git'),
    Alias('gln').to('git log -n').withTag('Git'),

    Alias('updategitbash').to(updateGitBashCommand).withTag('Update Git Bash').withScope(ConfigScope.WINDOWS),

    Alias('count').to('wc').addArg('-l').withTag('Quick count lines'),

    Alias('clip').to(copy).withTag('Clipboard'),
    Alias('paste').to(paste).pipe('tr -d').addArg(r'"\r"').withTag('Clipboard'),

    Alias('settings').to('code').addPath(MUREX_SETTINGS_JSON).withScope(ConfigScope.MUREX).withTag('MxSettings'),

    Variable(CURRENT_VERSION).withName('VERSION').withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Variable(OLD_VERSION).withName('OLD_VERSION').withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Alias('allMxVersions').to(RunPython(GQAF_SCRIPTS.slash('allMxVersions.py'))).withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Alias('version').to('echo $VERSION').withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Alias('versionUpgrade').to(RunPython(D_DRIVE.slash('Personal').slash('scripts').slash('upgradeVersion.py'))).withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Alias('richVersionView').to(RunPython(MUREX_CLI.slash('gqaf').slash('richVersionView.py'))).withScope(ConfigScope.MUREX).withTag('Status'),
    Alias('displayAlien').to(RunPython(MUREX_CLI.slash('display_alien').slash('excel_refresher.py')).andThen('start').addPath(MUREX_CLI.slash('display_alien').slash('display_alien.xlsx'))).withScope(ConfigScope.MUREX).withTag('Status'),
    Alias('richVersionViewCsv').to('richVersionView').addArg('--csv').addArg('> tmp.csv').andThen('start tmp.csv').withScope(ConfigScope.MUREX).withTag('Status'),
    Alias('safetyNetStatus').to(RunPython(MUREX_CLI.slash('gqaf').slash('safetyNetStatus.py'))).withScope(ConfigScope.MUREX).withTag('Status'),
    Alias('oldversion').to('echo $OLD_VERSION').withScope(ConfigScope.MUREX).withTag('MxVersion'),

    Alias('clipVersion').to('version').tee('clip').andThen('echo Copied.').withScope(ConfigScope.MUREX).withTag('MxVersion'),

    Alias('cdversion').to(cdInto('/d/$(version)')).withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Alias('startversion').to('start').addArg('/d/$(version)/mx-$(version).sln.lnk').withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Alias('startbpversion').to('start').addArg('/d/$(bpversion)/mx-$(bpversion).sln.lnk').withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Alias('cdapps').to(cdInto('/d/apps')).withScope(ConfigScope.MUREX).withTag('MxVersion'),
    Alias('appsversion').to(cdInto('/d/apps/$(version)*')).withScope(ConfigScope.MUREX).withTag('MxVersion'),

    Exec(f'echo Hello {USERNAME}!').withScope(ConfigScope.MUREX).withTag('Welcome message'),
    Exec('echo You are on ALIEN version').addArg('$(version)').withScope(ConfigScope.MUREX).withTag('Welcome message'),
    Exec('echo -e \n').withScope(ConfigScope.MUREX).withTag('Welcome message'),
    Exec(p4helperScript).addArg('--unmerged').muteOutput(2).withScope(ConfigScope.MUREX).withTag('Welcome message'),
    Exec('ls /u').muteOutput(3).ifFailed('echo "[WARNING]: Drives aren\'t mapped!"').withScope(ConfigScope.MUREX).withTag('Welcome message'),

    Alias('p4helper').to(p4helperScript).withScope(ConfigScope.MUREX).withTag('Perforce P4'),
    Alias('psubmit').to('p4helper').addArg('--submit').addArg('$(paste)').withScope(ConfigScope.MUREX).withTag('Perforce P4'),
    Alias('jira').to(jiraScript).withScope(ConfigScope.MUREX).withTag('Jira Request Handler'),
    Alias('jenkins').to(jenkinsScript).withScope(ConfigScope.MUREX).withTag('Jenkins Request Handler'),
    Alias('integrate').to(integrationScript).withScope(ConfigScope.MUREX).withTag('Integration Handler'),

    Alias('submit').to('p4helper --submit').withScope(ConfigScope.MUREX).withTag('Create a perfoce changelist from jira ID'),
    Alias('isItMerged').to('echo "looking for $(paste)..."').andThen('p4helper --me --build').pipe('greppaste').withScope(ConfigScope.MUREX).withTag('Quick check if defect is in mainstream'),

    Alias('mxbot').to('start').addArg(f'https://integrationweb.gqaf.fr.murex.com').withScope(ConfigScope.MUREX).withTag('Open MxBot Integration link'),
    Alias('ci').to('start').addArg(f'https://cje-core.fr.murex.com/assets/job/Alien/job/Git%20Alien/job/Git%20cpp%20build/').withScope(ConfigScope.MUREX).withTag('Open CI pipeline link'),
    Alias('pullRequest').to('start').addArg(f'https://stash.murex.com/projects/ASSETS/repos/alien/pull-requests?create').withScope(ConfigScope.MUREX).withTag('Open CI pipeline link'),
    Alias('freyja').to('start').addArg(f'https://cje-core.fr.murex.com/assets/job/FreyjaAlien/job/{CURRENT_VERSION}/').withScope(ConfigScope.MUREX).withTag('Open CI pipeline link'),

    Alias('mxOpen').to(RunPython(D_DRIVE.slash('Personal').slash('scripts').slash('mxOpen.py'))).withScope(ConfigScope.MUREX).withTag('MxOpen'),
    Alias('coco').to(RunPython(D_DRIVE.slash('Personal').slash('scripts').slash('mxOpen.py'))).addArg('--coconut').withScope(ConfigScope.MUREX).withTag('Search Coconut'),

    Alias('auth').to(RunPython(D_DRIVE.slash('Personal').slash('scripts').slash('auth.py'))).withScope(ConfigScope.MUREX).withTag('Auto Auth'),

    Alias('mde').to('D:\\.mxdevenvpp\\bin\\mde++.cmd').withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('mdeversion').to('mde about').pipe('grep -o').addArg('^0.[0-9]*.0.[0-9]*').withScope(ConfigScope.MUREX).withTag('Mxdevenv'),

    Alias('mdelatest').to(U_MXDEVENV.slash('latest').slash('mde++.cmd')).withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('mdelatestversion').to('mdelatest about').pipe('grep -o').addArg('^0.[0-9]*.0.[0-9]*').withScope(ConfigScope.MUREX).withTag('Mxdevenv'),

    Alias('umxdevenv').to(cdInto(U_MXDEVENV)).withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('dmxdevenv').to(cdInto(D_MXDEVENV)).withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('repomxdevenv').to(cdInto(REPO_MXDEVENV)).withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('murexcli').to(cdInto(MUREX_CLI)).withScope(ConfigScope.MUREX).withTag('Mxdevenv'),

    Alias('prepareVersion').to('mde prepareVersion').withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('prepareVersionFromClipBoard').to('mde prepareVersion -v $(paste) &').withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('versionManager').to('mde versionManager').inParallel().withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('logsVisualizer').to('mde logsVisualizer').inParallel().withScope(ConfigScope.MUREX).withTag('Mxdevenv'),
    Alias('setupsViewer').to('mde setupsViewer').withScope(ConfigScope.MUREX).withTag('Mxdevenv'),

    Alias('debugme').to('/d/apps/$(version)*/debugMe++.cmd').inParallel().withScope(ConfigScope.MUREX).withTag('Debugging'),

    Alias('drivesmapped').to('[ -d "/u" ]').then('echo $?').withScope(ConfigScope.MUREX).withTag('Drive Mapping'),
    Alias('unmapdrives').to('start').addPath(UNMAP_DRIVES_SCRIPT).withScope(ConfigScope.MUREX).withTag('Drive Mapping'),
    Alias('mapdrives').to('unmapdrives').delay(1).andThen('start').addPath(MAP_DRIVES_SCRIPT).delay(0.5).andThen('ls /u').withScope(ConfigScope.MUREX).withTag('Drive Mapping'),

    Alias('sessionInfo').to(RunPython(MUREX_CLI.slash('SessionInfo.py'))).withScope(ConfigScope.MUREX).withTag('Murex Session Info'),

    Alias('setups').to(RunPython(GQAF_SCRIPTS.slash('setups.py'))).withScope(ConfigScope.MUREX).withTag('GQAF API'),
    Alias('setupscsv').to('setups --csv 2>&1').grep('-vE').addQuoted(r'^getting|^fetching|^[0-9]|^\s*$').pipe('sed').addQuoted(r's/\s*,\s*/,/g').addArg('> tmp.csv && start tmp.csv').withScope(ConfigScope.MUREX).withTag('GQAF API'),
    Alias('pushsetups').to(RunPython(GQAF_SCRIPTS.slash('pushsetups.py'))).withScope(ConfigScope.MUREX).withTag('GQAF API'),
    Alias('pushsetupsAtHead').to('pushsetups').addArg('--head').addArg('--linux').withScope(ConfigScope.MUREX).withTag('GQAF API'),
    Alias('pushJobs').to(RunPython(GQAF_SCRIPTS.slash('pushJobs.py'))).withScope(ConfigScope.MUREX).withTag('GQAF API'),
    Alias('tpks').to(RunPython(GQAF_SCRIPTS.slash('jobs.py'))).withScope(ConfigScope.MUREX).withTag('GQAF API'),

    Alias('dtk').to('start').addPath('D:\\tools\\dtk\\tk.3.rc.1\\toolkit.bat').withScope(ConfigScope.MUREX).withTag('DTK'),

    Exec('ps aux').grep('ssh-agent').pipe('awk').addArg("'{print $1}'").pipe('xargs -r kill').withTag('Start Git SSH').withComment('Kill existing ssh-agents, if any'),
    Exec('eval "$(ssh-agent -s)"').muteOutput(3).withTag('Start Git SSH').withComment('Start a new ssh-agent for this session'),

    RunPython(REPO_ROOT.slash('src').slash('GlobalEnv.py')).muteOutput(3).addArg('--decrypt')\
        .andThen('ssh-add').addPath(REPO_ROOT.slash('encrypted').slash('github_key')).muteOutput(3).withTag('Start Git SSH')\
            .ifFailed('echo -n SSH Failed. config.json might contain a bad passphrase'),

    cdInto(REPO_MXDEVENV).withScope(ConfigScope.MUREX).withComment('Set git remote to use SSH for mxdevenv repo'),
    Exec('git remote set-url origin https://stash.murex.com/scm/devtools/mxdevenvpp.git').withScope(ConfigScope.MUREX),

    cdInto(REPO_ROOT).withComment('Set git remote to use SSH for EnvSync repo'),
    Exec('git remote set-url origin git@github.com:lebenebou/EnvSync.git'),

    ]

    if args.in_place:
        bashprofileContent: str = bashprofile.toString(scopeFilter=globalEnv.currentScope)
        ConfigFile.writeToFile(globalEnv.getBashProfilePath(), bashprofileContent)
    else:
        print(bashprofile.toString(), file=sys.stdout)

    exit(0)