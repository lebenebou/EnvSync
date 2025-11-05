
import os
import sys
import json

import time

from EnvSync.utils import zip, encryption, cli

def readJsonFile(filePath: str) -> dict:

    assert os.path.isfile(filePath), f'error while reading json, file does not exist: {filePath}'
    assert filePath.lower().endswith('.json'), f'not a json file: {filePath}'

    with open(filePath, 'r') as f:
        data = json.load(f)

    return data

from enum import IntFlag, auto
class ConfigScope(IntFlag):

    def _generate_next_value_(name, start, count, last_values):
        return 1 << count  # 1, 2, 4, 8, 16, ...

    MUREX = auto()
    LAPTOP = auto()
    HOME_PC = auto()

    WINDOWS = auto()
    LINUX = auto()

    NVIM = auto()
    OBSIDIAN = auto()

    COMMON = LAPTOP | MUREX | HOME_PC | WINDOWS | LINUX

    @staticmethod
    def getCurrentScope() -> 'ConfigScope':

        currentScope: ConfigScope = 0
        hostname: str = cli.commandOutput('hostname').strip()

        # detect OS
        if os.name == 'nt':
            currentScope |= ConfigScope.WINDOWS
        elif os.name == 'posix':
            currentScope |= ConfigScope.LINUX

        # detect machine
        if 'lebenebou' in hostname.lower():
            currentScope |= ConfigScope.LAPTOP

        elif hostname.lower() == 'dell163rws'.lower():
            currentScope |= ConfigScope.MUREX

        elif hostname.lower() == 'home-pc'.lower():
            currentScope |= ConfigScope.HOME_PC

        return currentScope

class GlobalEnv:

    _singletonInstance = None

    # singleton
    def __new__(globalEnv):

        if globalEnv._singletonInstance is None:
            print('[INIT] GlobalEnv', file=sys.stderr)
            globalEnv._singletonInstance = super().__new__(globalEnv)
            globalEnv._singletonInstance._initialized = False

        return globalEnv._singletonInstance

    def __init__(self):

        if self._initialized:
            return # singleton
            
        self._creationTime: float = time.perf_counter()
        self._initialized = True

        self.currentScope: ConfigScope = ConfigScope.getCurrentScope()
        self.hostname: str = cli.commandOutput('hostname').strip()

        self.loggingEnabled: bool = bool(0) # only set when tracing issues
        if self.loggingEnabled: print('[INIT] Initializing global env...', file=sys.stderr)

        self.repoRootPath = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.repoSrcPath = os.path.join(self.repoRootPath, 'src', 'EnvSync')
        self.configJsonFile = os.path.join(self.repoRootPath, 'config.json')
        self.encryptedPath = os.path.join(self.repoRootPath, 'encrypted')

        self.userHomeDir = os.path.expanduser('~')
        self._bashProfilePath: str = None
        self._vimRcPath: str = None

        self.gPavilion15Path = os.path.join('G:\\', 'Other computers', 'Pavilion15')

    def getBashProfilePath(self) -> str:

        if self._bashProfilePath is not None:
            return self._bashProfilePath

        print('Finding bashprofile file...', file=sys.stderr)

        options = ['.bash_profile', '.bashrc', '.profile']
        for filename in options:

            fullPath = os.path.join(self.userHomeDir, filename)
            if os.path.exists(fullPath):
                return fullPath

        print('[WARN] No bash profile file found in home directory.', file=sys.stderr)
        return None

    def getVimrcPath(self) -> str:

        if self._vimRcPath is not None:
            return self._vimRcPath

        print('Finding vimrc file...', file=sys.stderr)

        options = ['.vimrc', '_vimrc']
        for filename in options:

            fullPath = os.path.join(self.userHomeDir, filename)
            if os.path.exists(fullPath):
                return fullPath

        print('[WARN] No vimrc file found in home directory.', file=sys.stderr)
        return None

    def initJsonConfig(self):

        defaultConfig: dict = {
            "passphrase": None,
        }

        if os.path.isfile(self.configJsonFile):
            return

        print(f'[INFO] Creating config json: {self.configJsonFile}', file=sys.stderr)

        with open(self.configJsonFile, 'w') as f:
            json.dump(defaultConfig, f, indent=4)

    def getConfigValue(self, configName: str, valueIfNotFound: any = None) -> any:

        if not os.path.isfile(self.configJsonFile):
            self.initJsonConfig()

        configData: dict = readJsonFile(self.configJsonFile)
        return configData.get(configName, valueIfNotFound)

    def getEncryptionPassphrase(self, cmdFallback: bool = False) -> str:

        passphrase: str = self.getConfigValue('passphrase')
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

    def accessEncryptedFiles(self, cmdFallback: bool = False) -> int:

        if os.path.isdir(self.encryptedPath):
            return 0

        print('[INFO] Accessing encrypted files...', file=sys.stderr)

        tmpZipFile: str = os.path.join(self.repoRootPath, 'encrypted.zip')
        lockedZipFile: str = os.path.join(self.repoRootPath, 'encrypted.zip.locked')

        passphrase: str = self.getEncryptionPassphrase(cmdFallback=cmdFallback)
        returnCode: int = encryption.decryptFile(lockedZipFile, tmpZipFile, passphrase)

        if returnCode != 0:
            print('[ERROR] Could not access encrypted files. Bad passphrase?', file=sys.stderr)
            return returnCode

        zip.unzipFile(tmpZipFile, self.repoRootPath)
        os.remove(tmpZipFile)

        return 0

    def updateEncryptedFiles(self, commitMessage: str, cmdFallback: bool = False):

        repoRoot: str = self.repoRootPath
        cli.runCommand(command='git stash', workingDir=repoRoot)

        tmpZipFile: str = os.path.join(self.repoRootPath, 'encrypted.zip')
        lockedZipFile: str = os.path.join(self.repoRootPath, 'encrypted.zip.locked')

        zip.zipFolder(self.encryptedPath, tmpZipFile)
        passphrase: str = self.getEncryptionPassphrase(cmdFallback=cmdFallback)

        # overwrite encrypted.zip.locked
        encryption.encryptFile(tmpZipFile, lockedZipFile, passphrase)

        cli.runCommand(command=f'git add {lockedZipFile}', workingDir=repoRoot)
        cli.runCommand(command=f'git commit -m "{commitMessage}"', workingDir=repoRoot)
        cli.runCommand(command='git stash pop', workingDir=repoRoot)

        os.remove(tmpZipFile)

        returnCode: int = 0
        return returnCode

    # destructor
    def __del__(self):

        if self.loggingEnabled:
            print('[DEL] Deleting GlobalEnv singleton instance...', file=sys.stderr)

        elapsedMs: float = (time.perf_counter() - self._creationTime)*1000
        if elapsedMs < 10**3:
            print(f'\n{elapsedMs} ms', file=sys.stderr)
        else:
            print(f'\n{round(elapsedMs/1000, 1)} s', file=sys.stderr)

        return