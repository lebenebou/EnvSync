
import os, sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from utils import cli
from ai.agent import IterativeAgent, Model

import re

def createTempQueryFile(queryMessage: str) -> str:

    tempQueryFilePath = os.path.join(CURRENT_DIR, 'query.md')
    with open(tempQueryFilePath, 'w', encoding='utf-8') as f:
        f.write(queryMessage)

    return tempQueryFilePath

class OllamaModel(Model):
    def __init__(self, name: str):
        super().__init__(name)

    def checkAvailability(self) -> bool:

        res = cli.runCommand('ollama list')

        if res.returncode != 0:
            return False

        output: str = res.stdout
        return bool(re.search(rf'^{re.escape(self.name)}\s', output, re.MULTILINE))

    def run(self, queryMessage: str) -> str:

        result = cli.runCommand(f'ollama run {self.name} < "{createTempQueryFile(queryMessage)}"')
        assert result.returncode == 0, f"Failed to run model '{self.name}'. Error: {result.stderr}"
        return result.stdout

if __name__ == '__main__':

    ollama7b: Model = OllamaModel("qwen2.5-coder:14b")
    agent = IterativeAgent(ollama7b, verbose=True)

    agentQuery: str = "what is the purpose of the main.py of the finance project? please look inside that file and tell me how it operates"
    response: str = agent.ask(agentQuery)

    print(end="\n\n", file=sys.stderr, flush=True)
    print(response, file=sys.stdout, flush=True)