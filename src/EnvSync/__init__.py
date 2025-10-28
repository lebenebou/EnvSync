
import os
import sys
import json

from EnvSync.utils import zip, encryption, cli

def findBashProfilePath(homeDir: str) -> str:

    options = ['.bash_profile', '.bashrc', '.profile']
    for filename in options:

        fullPath = os.path.join(homeDir, filename)
        if os.path.exists(fullPath):
            return fullPath

    print('[WARN] No bash profile file found in home directory.', file=sys.stderr)
    return None

def findVimRcPath(homeDir: str) -> str:

    options = ['.vimrc', '_vimrc']
    for filename in options:

        fullPath = os.path.join(homeDir, filename)
        if os.path.exists(fullPath):
            return fullPath

    print('[WARN] No vimrc file found in home directory.', file=sys.stderr)
    return None

def readJsonFile(filePath: str) -> dict:

    assert os.path.isfile(filePath), f'error while reading json, file does not exist: {filePath}'
    assert filePath.lower().endswith('.json'), f'not a json file: {filePath}'

    with open(filePath, 'r') as f:
        data = json.load(f)

    return data

def initConfigJson(jsonFilePath: str):
    
    defaultConfig: dict = {
        "passphrase": None
    }

    if os.path.isfile(jsonFilePath):
        return

    print(f'[INFO] Creating config json: {jsonFilePath}', file=sys.stderr)
    with open(jsonFilePath, 'w') as f:
        json.dump(defaultConfig, f, indent=4)

class GlobalEnv:

    DEBUG_LOGS: bool = bool(0) # only set when tracing issues
    if DEBUG_LOGS: print('[INIT] Initializing global env...', file=sys.stderr)

    REPO_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    initConfigJson(os.path.join(REPO_ROOT_PATH, 'config.json'))

    REPO_SRC_PATH = os.path.join(REPO_ROOT_PATH, 'src', 'EnvSync')

    CONFIG_JSON_FILE = os.path.join(REPO_ROOT_PATH, 'config.json')

    ENCRYPTED_PATH = os.path.join(REPO_ROOT_PATH, 'encrypted')

    USER_HOME_DIR = os.path.expanduser('~')

    if DEBUG_LOGS: print('[INIT] Finding bashprofile file...', file=sys.stderr)
    BASH_PROFILE_PATH = findBashProfilePath(USER_HOME_DIR)
    if DEBUG_LOGS: print('[INIT] Finding vimrc file...', file=sys.stderr)
    VIM_RC_PATH = findVimRcPath(USER_HOME_DIR)

    G_PAVILION_15 = os.path.join('G:\\', 'Other computers', 'Pavilion15')

    @staticmethod
    def getConfigValue(configName: str, valueIfNotFound: any = None) -> any:

        configData: dict = readJsonFile(GlobalEnv.CONFIG_JSON_FILE)
        return configData.get(configName, valueIfNotFound)

    @staticmethod
    def getEncryptionPassphrase(cmdFallback: bool = False) -> str:
        
        passphrase: str = GlobalEnv.getConfigValue('passphrase')
        if passphrase:
            print('[INFO] Using encryption passphrase from config.json', file=sys.stderr)
            return passphrase

        if cmdFallback:
            print('No encryption passphrase found in config.json. Please input manually', file=sys.stderr)
            passphrase = input('Enter encryption passphrase: ')

        if not passphrase:
            print('[WARN] No encryption passphrase found.', file=sys.stderr)
            return None

        return passphrase

    @staticmethod
    def accessEncryptedFiles(cmdFallback: bool = False) -> int:

        if os.path.isdir(GlobalEnv.ENCRYPTED_PATH):
            return 0

        print('[INFO] Accessing encrypted files...', file=sys.stderr)

        tmpZipFile: str = os.path.join(GlobalEnv.REPO_ROOT_PATH, 'encrypted.zip')
        lockedZipFile: str = os.path.join(GlobalEnv.REPO_ROOT_PATH, 'encrypted.zip.locked')

        passphrase: str = GlobalEnv.getEncryptionPassphrase(cmdFallback=cmdFallback)
        returnCode: int = encryption.decryptFile(lockedZipFile, tmpZipFile, passphrase)

        if returnCode != 0:
            print('[ERROR] Could not access encrypted files. Bad passphrase?', file=sys.stderr)
            return returnCode

        zip.unzipFile(tmpZipFile, GlobalEnv.REPO_ROOT_PATH)
        os.remove(tmpZipFile)

        return 0

    @staticmethod
    def updateEncryptedFiles(commitMessage: str, cmdFallback: bool = False):

        repoRoot: str = GlobalEnv.REPO_ROOT_PATH
        cli.runCommand(command='git stash', workingDir=repoRoot)

        tmpZipFile: str = os.path.join(GlobalEnv.REPO_ROOT_PATH, 'encrypted.zip')
        lockedZipFile: str = os.path.join(GlobalEnv.REPO_ROOT_PATH, 'encrypted.zip.locked')

        zip.zipFolder(GlobalEnv.ENCRYPTED_PATH, tmpZipFile)
        passphrase: str = GlobalEnv.getEncryptionPassphrase(cmdFallback=cmdFallback)

        # overwrite encrypted.zip.locked
        encryption.encryptFile(tmpZipFile, lockedZipFile, passphrase)

        cli.runCommand(command=f'git add {lockedZipFile}', workingDir=repoRoot)
        cli.runCommand(command=f'git commit -m "{commitMessage}"', workingDir=repoRoot)
        cli.runCommand(command='git stash pop', workingDir=repoRoot)

        os.remove(tmpZipFile)

        returnCode: int = 0
        return returnCode