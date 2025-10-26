
import os
import sys

def findBashProfilePath(homeDir: str) -> str:

    options = ['.bash_profile', '.bashrc', '.profile']
    for filename in options:

        fullPath = os.path.join(homeDir, filename)
        if os.path.exists(fullPath):
            return fullPath

    print("[WARN]: No bash profile file found in home directory.", file=sys.stderr)
    return None

def findVimRcPath(homeDir: str) -> str:

    options = ['.vimrc', '_vimrc']
    for filename in options:

        fullPath = os.path.join(homeDir, filename)
        if os.path.exists(fullPath):
            return fullPath

    print("[WARN]: No vimrc file found in home directory.", file=sys.stderr)
    return None

class EnvValues:

    REPO_ROOT_PATH = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    REPO_SRC_PATH = os.path.join(REPO_ROOT_PATH, 'src', 'EnvSync')

    USER_HOME_DIR = os.path.expanduser('~')

    BASH_PROFILE_PATH = findBashProfilePath(USER_HOME_DIR)
    VIM_RC_PATH = findVimRcPath(USER_HOME_DIR)

    G_PAVILION_15 = os.path.join('G:\\', 'Other computers', 'Pavilion15')