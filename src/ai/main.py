
import os, sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from utils import cli
from ai.agent import IterativeAgent, Model

import re
import tempfile

class OllamaModel(Model):
    def __init__(self, name: str):
        super().__init__(name)
        self._tempFile = tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.md', encoding='utf-8')
        self._tempFilePath = self._tempFile.name

    def checkAvailability(self) -> bool:

        res = cli.runCommand('ollama list')

        if res.returncode != 0:
            return False

        output: str = res.stdout
        return bool(re.search(rf'^{re.escape(self.name)}\s', output, re.MULTILINE))

    def run(self, queryMessage: str) -> str:

        self._tempFile.seek(0)
        self._tempFile.write(queryMessage)
        self._tempFile.truncate()
        self._tempFile.flush()

        result = cli.runCommand(f'ollama run {self.name} < "{self._tempFilePath}"')
        assert result.returncode == 0, f"Failed to run model '{self.name}'. Error: {result.stderr}"
        return result.stdout

    def __del__(self):

        try:
            self._tempFile.close()
            os.unlink(self._tempFilePath)
        except Exception as e:
            print(f"Error cleaning up temporary file: {e}", file=sys.stderr)

if __name__ == '__main__':

    ollama7b: Model = OllamaModel("qwen2.5-coder:7b")
    agent = IterativeAgent(ollama7b, verbose=True)

    agentQuery: str = "Am I connected to the internet?"
    response: str = agent.ask(agentQuery)

    print(response, file=sys.stdout, flush=True)