
import os
import sys
import json

def findBashProfilePath(homeDir: str) -> str:

    options = ['.bash_profile', '.bashrc', '.profile']
    for filename in options:

        fullPath = os.path.join(homeDir, filename)
        if os.path.exists(fullPath):
            return fullPath

    print('[WARN]: No bash profile file found in home directory.', file=sys.stderr)
    return None

def findVimRcPath(homeDir: str) -> str:

    options = ['.vimrc', '_vimrc']
    for filename in options:

        fullPath = os.path.join(homeDir, filename)
        if os.path.exists(fullPath):
            return fullPath

    print('[WARN]: No vimrc file found in home directory.', file=sys.stderr)
    return None

def readJsonFile(filePath: str) -> dict:

    assert os.path.isfile(filePath), f'error while reading json, file does not exist: {filePath}'
    assert filePath.lower().endswith('.json'), f'not a json file: {filePath}'

    with open(filePath, 'r') as f:
        data = json.load(f)

    return data

class GlobalEnv:

    REPO_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    REPO_SRC_PATH = os.path.join(REPO_ROOT_PATH, 'src', 'EnvSync')

    CONFIG_JSON_FILE = os.path.join(REPO_ROOT_PATH, 'config.json')
    CONFIG_DATA: dict = readJsonFile(CONFIG_JSON_FILE)
    LOG_VERBOSITY: int = CONFIG_DATA.get('log_verbosity', 0)

    ENCRYPTED_PATH = os.path.join(REPO_ROOT_PATH, 'encrypted')
    DECRYPTED_PATH = os.path.join(REPO_ROOT_PATH, 'decrypted')

    USER_HOME_DIR = os.path.expanduser('~')

    BASH_PROFILE_PATH = findBashProfilePath(USER_HOME_DIR)
    VIM_RC_PATH = findVimRcPath(USER_HOME_DIR)

    G_PAVILION_15 = os.path.join('G:\\', 'Other computers', 'Pavilion15')

    @staticmethod
    def getConfigValue(configName: str, defaultValue: any = None) -> any:
        return GlobalEnv.CONFIG_DATA.get(configName, None)

    @staticmethod
    def getEcryptionPassphrase(cmdFallback: bool = False) -> str:
        
        passphrase: str = GlobalEnv.getConfigValue('passphrase')
        if passphrase:
            return passphrase

        if cmdFallback:
            print('No encryption passphrase found in config.json. Please input manually', file=sys.stderr)
            passphrase = input('Enter encryption passphrase: ')

        if not passphrase:
            print('[WARN]: No encryption passphrase found.', file=sys.stderr)

        return passphrase

    @staticmethod
    def encryptFile(inputFile: str, outputFile: str, passphrase: str):

        assert False, 'Not implemented yet'

    @staticmethod
    def encryptFiles(deleteDecryptedWhenDone: bool = False, cmdFallback: bool = False):

        passphrase: str = GlobalEnv.getEcryptionPassphrase(cmdFallback)

        for root, dirs, files in os.walk(GlobalEnv.DECRYPTED_PATH):

            for file in files:

                decryptedFilePath = os.path.join(root, file)
                relativePath = os.path.relpath(decryptedFilePath, GlobalEnv.DECRYPTED_PATH)
                encryptedFilePath = os.path.join(GlobalEnv.ENCRYPTED_PATH, relativePath + '.age')

                os.makedirs(os.path.dirname(encryptedFilePath), exist_ok=True)

                GlobalEnv.encryptFile(decryptedFilePath, encryptedFilePath, passphrase)

                if deleteDecryptedWhenDone:
                    os.remove(decryptedFilePath)

                continue

            continue

        return

    @staticmethod
    def decryptFiles(cmdFallback: bool = False):
        pass