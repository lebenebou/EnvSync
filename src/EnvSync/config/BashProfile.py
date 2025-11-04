
import os
import sys
import argparse

from EnvSync.config.Aliases import *
from EnvSync import GlobalEnv

CURRENT_FILE = os.path.abspath(__file__)

import json
def readJsonFromFile(filePath: str) -> dict:
    with open(filePath, 'r') as file:
        return json.load(file)

if __name__ == "__main__":

    # parse args
    parser = argparse.ArgumentParser(description='Update your bashprofile through Python')

    optionGroup = parser.add_mutually_exclusive_group()
    optionGroup.add_argument('--in_place', action='store_true', help='Directly modify ~/.bash_profile')
    optionGroup.add_argument('--force_scope', type=int, help='Mock run in a custom scope', required=False, default=CURRENT_SCOPE)

    args = parser.parse_args()
    if CURRENT_SCOPE != args.force_scope:
        CURRENT_SCOPE = args.force_scope

    # Paths
    D_DRIVE = Path("D:\\").withName('D Drive').withScope(ConfigOption.COMMON)
    C_DRIVE = Path("C:\\").withName('C Drive').withScope(ConfigOption.COMMON)

    globalEnv = GlobalEnv()
    REPO_ROOT = Path(globalEnv.repoRootPath).withName('REPO ROOT PATH')
    SRC_PATH = Path(globalEnv.repoSrcPath).withName('SRC PATH')

    UTILS_PATH = SRC_PATH.slash('utils').withName('UTILS PATH')

    G_DRIVE = Path("G:\\").withName('G Drive').withScope(ConfigOption.COMMON)
    ONEDRIVE_MUREX = Path("D:\\OneDrive - Murex").withName('ONEDRIVE').withScope(ConfigOption.MUREX)

    DESKTOP = Path(os.path.join(globalEnv.userHomeDir, 'Desktop')).withName('DESKTOP').withScope(ConfigOption.LAPTOP).withAlternateValueForScope(ConfigOption.MUREX, ONEDRIVE_MUREX.slash('Desktop'))
    DOWNLOADS = Path(os.path.join(globalEnv.userHomeDir, 'Downloads')).withName('DOWNLOADS').withScope(ConfigOption.LAPTOP).withAlternateValueForScope(ConfigOption.MUREX, ONEDRIVE_MUREX.slash('Downloads'))
    DOCUMENTS = Path('C:\\Users\\yyamm\\Documents\\MyDocuments').withName('DOCUMENTS').withScope(ConfigOption.LAPTOP).withAlternateValueForScope(ConfigOption.MUREX, os.path.join(globalEnv.gPavilion15Path, 'MyDocuments'))

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
    Alias('money').to(RunPython(SRC_PATH.slash('finance').slash('parser.py'))).withTag('Personal'),
    Alias('updatemoney').to('money').addArg('--refresh').withTag('Personal'),

    Alias('grep').to('grep -i --color --binary-files=without-match --exclude-dir=".git"').withTag('Grep default options'),
    Alias('grepdefects').to('grep').addArg('-Eo').addQuoted('DEF[0-9]+').withTag('grep').withScope(ConfigOption.MUREX),

    InlinePython(runImmediately=True).linesAre([
        'import pyautogui',
        'pyautogui.hotkey("win", "up")',
        'pyautogui.hotkey("ctrl", "+")',
        'pyautogui.hotkey("ctrl", "+")',
        'pyautogui.hotkey("ctrl", "+")',
    ]),

    cdInto(globalEnv.userHomeDir).withScope(ConfigOption.LAPTOP).withTag("Init"),
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

    Alias('exp').to(RunPython(UTILS_PATH.slash('exp.py'))),
    Alias('start').to(RunPython(UTILS_PATH.slash('start.py'))),
    Alias('win').to(RunPython(UTILS_PATH.slash('win.py'))),

    Function('restart').thenExecute([
        Exec('win 2').disown(),
        Exec('exit'),
        ]).withTag('bash'),

    Alias('reload').to('updatebashprofile').andThen('restart').withTag('bash'),
    Alias('cat').to('bat').withTag('bash'),
    Alias('json').to('bat --language=json').withTag('bash'),
    Alias('csv').to('bat --language=csv').withTag('bash'),
    Alias(':r').to('restart').withTag('bash'),
    Alias(':q').to('win 2').andThen('exit').withTag('bash'),
    Alias('bashprofile').to('code').addPath(globalEnv.getBashProfilePath()).withTag('bash'),

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

    Alias('editvimrc').to('code').addPath(globalEnv.getVimrcPath()).withTag('Config'),
    Alias('editbashprofile').to('code').addPath(CURRENT_FILE).withTag('Config'),
    Alias('runbashprofile').to(RunPython(CURRENT_FILE)).withTag('Config'),
    Alias('updatebashprofile').to(RunPython(CURRENT_FILE)).addArg('--in_place').withTag('Config'),

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
    Alias('displayAlien').to(RunPython(MUREX_CLI.slash('display_alien').slash('excel_refresher.py')).andThen('start').addPath(MUREX_CLI.slash('display_alien').slash('display_alien.xlsx'))).withScope(ConfigOption.MUREX).withTag('Status'),
    Alias('richVersionViewCsv').to('richVersionView').addArg('--csv').addArg('> tmp.csv').andThen('start tmp.csv').withScope(ConfigOption.MUREX).withTag('Status'),
    Alias('safetyNetStatus').to(RunPython(MUREX_CLI.slash('gqaf').slash('safetyNetStatus.py'))).withScope(ConfigOption.MUREX).withTag('Status'),
    Alias('oldversion').to('echo $OLD_VERSION').withScope(ConfigOption.MUREX).withTag('MxVersion'),

    Alias('clipVersion').to('version').tee('clip').andThen('echo Copied.').withScope(ConfigOption.MUREX).withTag('MxVersion'),

    Alias('cdversion').to(cdInto('/d/$(version)')).withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('startversion').to('start').addArg('/d/$(version)/mx-$(version).sln.lnk').withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('startbpversion').to('start').addArg('/d/$(bpversion)/mx-$(bpversion).sln.lnk').withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('cdapps').to(cdInto('/d/apps')).withScope(ConfigOption.MUREX).withTag('MxVersion'),
    Alias('appsversion').to(cdInto('/d/apps/$(version)*')).withScope(ConfigOption.MUREX).withTag('MxVersion'),

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
        ConfigFile.writeToFile(globalEnv.getBashProfilePath(), bashprofileContent)
    else:
        print(bashprofile.toString(), file=sys.stdout)

    exit(0)