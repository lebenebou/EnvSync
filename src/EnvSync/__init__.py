
import os
import sys
import json

from EnvSync.utils import zip, encryption

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

class GlobalEnv:

    DEBUG_LOGS: bool = bool(0) # only set when tracing issues
    if DEBUG_LOGS: print('[INIT] Initializing global env...', file=sys.stderr)

    REPO_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    def getEcryptionPassphrase(cmdFallback: bool = False) -> str:
        
        passphrase: str = GlobalEnv.getConfigValue('passphrase')
        if passphrase:
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

        print('Accessing encrypted files...', end='\r', file=sys.stderr)

        if os.path.isdir(GlobalEnv.ENCRYPTED_PATH):
            print('[INFO] Already decrypted.', file=sys.stderr)
            return 0

        tmpZipFile: str = os.path.join(GlobalEnv.REPO_SRC_PATH, 'encrypted.zip')
        lockedZipFile: str = os.path.join(GlobalEnv.REPO_SRC_PATH, 'encrypted.zip.locked')

        passphrase: str = GlobalEnv.getEcryptionPassphrase(cmdFallback=cmdFallback)
        returnCode: int = encryption.decryptFile(lockedZipFile, tmpZipFile, passphrase)

        if returnCode != 0:
            print('[ERROR] Could not access encrypted files. Bad passphrase?', file=sys.stderr)
            return returnCode

        zip.unzipFile(tmpZipFile, GlobalEnv.REPO_ROOT_PATH)
        os.remove(tmpZipFile)

        return 0

    @staticmethod
    def updateEncryptedFiles(CommitMessage: str, cmdFallback: bool = False):

        tmpZipFile: str = os.path.join(GlobalEnv.REPO_SRC_PATH, 'encrypted.zip')
        lockedZipFile: str = os.path.join(GlobalEnv.REPO_SRC_PATH, 'encrypted.zip.locked')

        zip.zipFolder(GlobalEnv.ENCRYPTED_PATH, tmpZipFile)
        passphrase: str = GlobalEnv.getEcryptionPassphrase(cmdFallback=cmdFallback)
        encryption.encryptFile(tmpZipFile, lockedZipFile, passphrase)

        os.remove(tmpZipFile)

        returnCode: int = 0
        return returnCode