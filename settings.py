
import sys

# Sanity Checks ---
if sys.version_info < (3, 6, 8):
    print(f'Your python version is too old! ({sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]})', file=sys.stderr)
    print(f'Python 3.6.8 or higher is required', file=sys.stderr)
    exit(1)

try:
    import requests
except ImportError:
    print(f'requests is not installed. Try: pip install requests', file=sys.stderr)
    exit(1)

try:
    import tabulate
except ImportError:
    print(f'tabulate is not installed. Try: pip install tabulate', file=sys.stderr)
    exit(1)

try:
    import urllib3
except ImportError:
    print(f'urllib3 is not installed. Try: pip install urllib3', file=sys.stderr)
    exit(1)

try:
    from dateutil.parser import isoparse
except ImportError:
    print(f'dateutil is not installed. Try: pip install python-dateutil', file=sys.stderr)
    exit(1)
# --- Sanity Checks

import re
import json
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
import cli

from typing import Dict

SETTINGS_FILE = os.path.join("D:\\", ".mxdevenvpp", "settings", "python_scripts_settings.json")

def loadSettings(filePath: str) -> dict:

    if not os.path.exists(filePath):
        print(f'Did not find settings file: {filePath}', file=sys.stderr)
        return initSettingsFile(filePath)

    with open(SETTINGS_FILE, "r") as settingsFile:
        
        settings = json.load(settingsFile)
        return settings

def initSettingsFile(filePath: str) -> dict:

    print(f'Creating settings file: {filePath}', file=sys.stderr)

    settings = {}

    settings['username'] = 'user'

    p4InfoCommand = cli.runCommand('p4 info')
    if p4InfoCommand.returncode != 0:
        print(f"Since you don't have perforce, we don't know who you are :(", file=sys.stderr)
    else:
        p4InfoOutput = p4InfoCommand.stdout
        settings['username'] = re.search(r"user\s*name:\s+(\S+)", p4InfoOutput, flags=re.IGNORECASE).group(1)

    settings['password'] = None
    settings['version'] = None
    settings['gqaf_token'] = None
    settings['version_id_cache'] = {}

    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings, file, indent=4)

    return settings

def getSettingsFilePath() -> str:
    return SETTINGS_FILE

def getSetting(settingName: str) -> any:

    settings = loadSettings(SETTINGS_FILE)
    return settings[settingName]

def setSetting(settingName: str, newValue: any):

    settings = loadSettings(SETTINGS_FILE)
    assert settingName in settings, f"Trying to set a setting which does not exist: {settingName}"

    settings[settingName] = newValue
    with open(SETTINGS_FILE, 'w') as file:
        json.dump(settings, file, indent=4)
    
# --- SETTING GETTERS ---
def getCurrentVersion() -> str:
    return getSetting("version")

def getVersionValidationId(version: str) -> str:
    return getSetting("version_id_cache").get(version, "")

def getPreviousVersion() -> str:
    return getSetting("previous_version")

def getUsername() -> int:
    return getSetting("username")

def getEncryptedPassword() -> str:
    return getSetting("password")

def getGqafApiToken() -> str:
    return getSetting("gqaf_token")

def getJenkinsApiToken() -> str:
    return getSetting("jenkins_token")

def getMxBotNotificationList() -> str:
    return getSetting("mxbot_notification_list")

def getVersionIdCache() -> Dict[str, str]:
    return getSetting("version_id_cache")

def cacheVersionAtok(version: str, atok: str):

    cache: dict = getSetting("version_id_cache")
    cache[version] = atok
    setSetting("version_id_cache", cache)

def refreshVersionValidationId():

    # TODO
    return None

def upgradeVersion(newVersion: str):

    newVersion = newVersion.strip()
    oldVersion = getCurrentVersion()

    if oldVersion == newVersion:
        print(f'Old & New version are equal: {newVersion}', file=sys.stderr)
        return

    print(f'Old version: {oldVersion}', file=sys.stderr)
    setSetting("previous_version", oldVersion)

    setSetting("version", newVersion)
    print(f'New version: {newVersion}', file=sys.stderr)

if __name__ == '__main__':

    print(f'Hello, {getUsername()}!', file=sys.stderr)
    print(f'Your settings file is in: {SETTINGS_FILE}', file=sys.stderr)