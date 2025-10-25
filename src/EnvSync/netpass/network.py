
import re
import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)
from EnvSync.utils import cli

import time
import json

def epochTime() -> int:
    return int(time.time())

class Network:

    nameRegex = r"^\s*All User Profile\s*: (.*)$"
    passwordRegex = r"^\s*Key Content\s+: (.*)$"

    def __init__(self, name: str):
        
        self.name = name
        self.password = None

    def fetchPassword(self) -> str:
        
        command = f'netsh wlan show profiles name="{self.name}" key=clear | findstr /I "content"'
        result = cli.runCommand(command)

        if result.returncode != 0:
            return self.password

        self.password = re.search(Network.passwordRegex, result.stdout).group(1)
        return self.password

@staticmethod
def getNetworks(nameFilter: str = None) -> list[Network]:

    command = f'netsh wlan show profiles'
    if nameFilter:
        nameFilter.strip().strip('"').strip()
        command += f' | findstr /I "{nameFilter}"'

    result = cli.runCommand(command)

    if result.returncode != 0:
        return []

    matches = re.findall(Network.nameRegex, result.stdout, re.MULTILINE)

    return [Network(match) for match in matches]

@staticmethod
def getNetworksWithPasswords(nameFilter = None) -> list[Network]:

    networks = getNetworks(nameFilter)
    [network.fetchPassword() for network in networks]

    return networks

@staticmethod
def toJson(networks: list[Network]) -> str:

    d = {"epochTimestamp": epochTime(), "networks": []}

    for network in networks:
        d["networks"].append({"name": network.name, "password": network.password})

    return json.dumps(d, indent=4)

if __name__ == "__main__":

    print(toJson(getNetworksWithPasswords()))