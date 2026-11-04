
import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

from utils import cli
from agents import Model

import re
import ollama


class OllamaModel(Model):
    def __init__(self, name: str):
        super().__init__(name)

    def checkAvailability(self) -> bool:
        raise NotImplementedError("You cannot use an abstract model instance.")

    def run(self, queryMessage: str, response_format: dict = None) -> str:

        response = ollama.chat(
            model=self.name,
            messages=[{'role': 'user', 'content': queryMessage}],
            format=response_format,
            options={"temperature": 0}
        )

        return response.message.content

class OllamaLocalModel(OllamaModel):
    def checkAvailability(self) -> bool:

        res = cli.runCommand('ollama list')

        if res.returncode != 0:
            return False

        output: str = res.stdout
        return bool(re.search(rf'^{re.escape(self.name)}\s', output, re.MULTILINE))

class OllamaCloudModel(OllamaModel):
    def checkAvailability(self) -> bool:

        internetAvailable: bool = cli.runCommand('curl -s --head --connect-timeout 2 google.com').returncode == 0
        if not internetAvailable:
            return False

        signedIn: bool = cli.runCommand('ollama signin').returncode == 0
        if not signedIn:
            return False

        return OllamaLocalModel.checkAvailability(self)