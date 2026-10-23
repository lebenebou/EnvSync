
import sys, os
import argparse
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from GlobalEnv import GlobalEnv

import json
def jsonToDict(jsonFile: str) -> dict:

    assert os.path.exists(jsonFile), "File does not exist: " + jsonFile
    assert jsonFile.endswith(".json"), "File must be a JSON file"

    with open(jsonFile, "r") as f:
        return json.load(f)

class Credential:

    def __init__(self, credential_name, username, password):
        self.credential_name = credential_name
        self.username = username
        self.password = password

    def __str__(self):

        s = f"Credential: {self.credential_name}"

        if self.username:
            s += f"\n\tUsername: {self.username}"

        if self.password:
            s += f"\n\tPassword: {self.password}"

        return s

def credentialsFromJsonFile(jsonFile: str) -> list[Credential]:

    data = jsonToDict(jsonFile)

    credentials = []
    for item in data:

        c = Credential(
            credential_name=item.get("credential_name"),
            username=item.get("username"),
            password=item.get("password")
        )

        credentials.append(c)
        continue

    return credentials


if __name__ == "__main__":

    dycryptSuccess: int = GlobalEnv().accessEncryptedFiles(cmdFallback=True)

    if dycryptSuccess != 0:
        print("Failed to access credentials.")
        exit(1)

    credentials: list[Credential] = credentialsFromJsonFile(os.path.join(GlobalEnv().encryptedPath, "credentials.json"))

    parser = argparse.ArgumentParser()
    parser.add_argument("pattern", nargs="?", default=".*")
    args = parser.parse_args()

    pattern = re.compile(args.pattern, re.IGNORECASE)

    if len(credentials) == 0:
        print('No credentials found.')
        exit(0)

    print(file=sys.stderr)

    for credential in credentials:
        if pattern.search(credential.credential_name):
            print(credential, end="\n\n")
