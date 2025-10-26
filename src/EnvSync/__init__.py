
import os
import sys
import json

import shutil
import subprocess

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

    DEBUG_LOGS: bool = False

    REPO_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    REPO_SRC_PATH = os.path.join(REPO_ROOT_PATH, 'src', 'EnvSync')

    CONFIG_JSON_FILE = os.path.join(REPO_ROOT_PATH, 'config.json')

    ENCRYPTED_PATH = os.path.join(REPO_ROOT_PATH, 'encrypted')
    DECRYPTED_PATH = os.path.join(REPO_ROOT_PATH, 'decrypted')

    USER_HOME_DIR = os.path.expanduser('~')

    BASH_PROFILE_PATH = findBashProfilePath(USER_HOME_DIR)
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

        return passphrase

    @staticmethod
    def encryptFile(inputFile: str, outputFile: str, passphrase: str):

        assert os.path.isfile(inputFile), f'cannot ecnrypt file that does not exist: {inputFile}'

        command = f'openssl enc -aes-256-cbc -pbkdf2 -in {inputFile} -out {outputFile} -pass pass:{passphrase}'
        result = subprocess.run(command.split())

        if result.returncode != 0:
            print(f'[ERROR] Failed to encrypt file: {inputFile}', file=sys.stderr)
            return

        return

    @staticmethod
    def decryptFile(inputFile: str, outputFile: str, passphrase: str) -> int:

        assert os.path.isfile(inputFile), f'cannot decrypt file that does not exist: {inputFile}'

        command = f'openssl enc -d -aes-256-cbc -pbkdf2 -in {inputFile} -out {outputFile} -pass pass:{passphrase}'
        result = subprocess.run(command.split())

        if result.returncode != 0:
            print(f'[ERROR] Failed to decrypt file: {inputFile}', file=sys.stderr)
            return result.returncode
        
        return 0

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
    def decryptFiles(overwriteDecryptedDir: bool = False, cmdFallback: bool = False):
        
        if not overwriteDecryptedDir and os.path.exists(GlobalEnv.DECRYPTED_PATH):
            print(f'[WARN] Decrypted directory already exists: {GlobalEnv.DECRYPTED_PATH}', file=sys.stderr)
            print(f'[WARN] NO DECRYPTION was done.', file=sys.stderr)
            return

        if overwriteDecryptedDir and os.path.exists(GlobalEnv.DECRYPTED_PATH):
            shutil.rmtree(GlobalEnv.DECRYPTED_PATH, ignore_errors=False)

        passphrase: str = GlobalEnv.getEcryptionPassphrase(cmdFallback)

        for root, dirs, files in os.walk(GlobalEnv.ENCRYPTED_PATH):

            encryptedFiles = (f for f in files if f.endswith('.age'))
            for file in encryptedFiles:

                encryptedFilePath = os.path.join(root, file)
                relativePath = os.path.relpath(encryptedFilePath, GlobalEnv.ENCRYPTED_PATH)
                decryptedFilePath = os.path.join(GlobalEnv.DECRYPTED_PATH, relativePath[:-4])  # remove .age

                os.makedirs(os.path.dirname(decryptedFilePath), exist_ok=True)

                errorCode = GlobalEnv.decryptFile(encryptedFilePath, decryptedFilePath, passphrase)

                if errorCode == 0:
                    continue

                elif errorCode == 1:
                    print(f'Bad passphrase. Cannot decrypt files', file=sys.stderr)
                    return

                else:
                    print(f'[ERROR] Could not dectypt file: {encryptedFilePath}', file=sys.stderr)

                continue

            continue