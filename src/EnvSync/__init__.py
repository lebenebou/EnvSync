
import os
import sys
import json

from dataclasses import dataclass, field
import subprocess

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

@dataclass(frozen=True) # these values cannot be changed
class GlobalEnv:

    REPO_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    REPO_SRC_PATH = os.path.join(REPO_ROOT_PATH, 'src', 'EnvSync')

    CONFIG_JSON_FILE = os.path.join(REPO_ROOT_PATH, 'config.json')
    CONFIG_DATA: dict = field(default_factory=lambda: readJsonFile(GlobalEnv.CONFIG_JSON_FILE)) # a CONST dict

    ENCRYPTED_PATH = os.path.join(REPO_ROOT_PATH, 'encrypted')
    DECRYPTED_PATH = os.path.join(REPO_ROOT_PATH, 'decrypted')

    USER_HOME_DIR = os.path.expanduser('~')

    BASH_PROFILE_PATH = findBashProfilePath(USER_HOME_DIR)
    VIM_RC_PATH = findVimRcPath(USER_HOME_DIR)

    G_PAVILION_15 = os.path.join('G:\\', 'Other computers', 'Pavilion15')

    @staticmethod
    def getConfigValue(configName: str) -> any:
        return GlobalEnv.CONFIG_DATA.get(configName, None)

    @staticmethod
    def getEcryptionPassphrase(cmdFallback: bool = False) -> str:
        
        passphrase: str = GlobalEnv.getConfigValue('passphrase')
        if passphrase:
            return passphrase

        if cmdFallback:
            print('No encryption passphrase found in config.json. Please input manually', file=sys.stderr)
            passphrase = input('Enter encryption passphrase: ')

        return passphrase

    @staticmethod
    def encryptFiles(deleteDecrypted: bool = False, cmdFallback: bool = False):
    
        for root, dirs, files in os.walk(GlobalEnv.DECRYPTED_PATH):

            for file in files:

                decryptedFilePath = os.path.join(root, file)
                relativePath = os.path.relpath(decryptedFilePath, GlobalEnv.DECRYPTED_PATH)
                encryptedFilePath = os.path.join(GlobalEnv.ENCRYPTED_PATH, relativePath + '.age')

                os.makedirs(os.path.dirname(encryptedFilePath), exist_ok=True)

                passphrase: str = GlobalEnv.getEcryptionPassphrase(cmdFallback)
                result = subprocess.run(
                    [ 'age', decryptedFilePath, '-o', encryptedFilePath, '-p'],
                    input=passphrase.encode(),
                    check=True
                    )

                if result.returncode != 0:
                    print(f'[ERROR]: Failed to encrypt file: {decryptedFilePath}', file=sys.stderr)
                    continue

                if deleteDecrypted:
                    os.remove(decryptedFilePath)

                continue

            continue

    @staticmethod
    def decryptFiles(cmdFallback: bool = False):
        pass