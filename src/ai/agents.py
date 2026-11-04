
import os, sys, json
from typing import Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from utils import cli
from subprocess import CompletedProcess

from pydantic import BaseModel, Field, model_validator
from enum import IntEnum, auto

class CommandImpact(IntEnum):

    Minimal = auto()
    Medium = auto()
    Dangerous = auto()

    @staticmethod
    def measure(command: str) -> 'CommandImpact':

        impactMap = {

        CommandImpact.Minimal:
            [
            ],

        CommandImpact.Medium:
            [
                "git reset",
                "git stash",
                "git checkout",
                "git add",
                "git commit",
                "pip",
                "winget",
                "npm",
                "yarn",
                "mkdir",
                "cp",
                "copy",
                "mv",
                "move",
                "chmod",
                "chown",
            ],

        CommandImpact.Dangerous:
            [
                "rm",
                "rmdir",
                "del",
                "shutil",
                "format",
                "diskpart",
                "mkfs",
                "dd",
                "net user /delete",
                "reg delete",
                "erase",
            ],

        }

        highestImpact = CommandImpact.Minimal

        for impact, argList in impactMap.items():
            for arg in argList:
                
                if arg.lower() in command.lower():
                    highestImpact = max(highestImpact, impact)

                continue

            continue

        return highestImpact

class AgentResponse(BaseModel):
    reply: str = ""
    commands: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_response(self):
        if not self.reply and not self.commands:
            raise ValueError("Response must contain a reply or commands")
        return self

def completedProcessToDict(proc: CompletedProcess) -> dict:
    return {
        "command": " ".join(proc.args) if isinstance(proc.args, list) else proc.args,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "returnCode": proc.returncode
    }


class Model:
    def __init__(self, name: str):
        self.name: str = name
        self.isAvailable: bool = self.checkAvailability()

        assert isinstance(self.isAvailable, bool), "The _checkModelAvailability method must return a boolean value"
        assert self.isAvailable, f"Model '{self.name}' is not available."

    def checkAvailability(self) -> bool:
        raise NotImplementedError("You must implement the check availability method in subclasses of Model")

    def run(self, queryMessage: str, response_format: Optional[dict] = None) -> str:
        raise NotImplementedError("You must implement the run method in subclasses of Model")

class IterativeAgent:

    class Query:
        def __init__(self, queryMessage: str):
            self.queryMessage: str = queryMessage
            self.previouslyRunCommands: list[CompletedProcess] = []
            self.previouslyRunCommands.append(cli.runCommand('pwd'))

        def toString(self) -> str:
            res: str = "You are helping a human with a request, they're asking:\n"
            res += f'"{self.queryMessage}"\n\n'

            res += "If you believe that you can help them further by running some commands on their machine,\n"
            res += "then reply in a JSON format with 'reply' and 'commands' fields.\n\n"
            res += "Do not suggest commands with placeholders. If you need the results of some commands before executing other ones, reply with those first, then those will be run and you will have their results\n"

            if len(self.previouslyRunCommands) > 0:
                res += "\nAs a reminder, here are the commands that you have already run, in order to discover more about their environment:"
                history = [
                    completedProcessToDict(proc)
                    for proc in self.previouslyRunCommands
                ]
                res += f"\n```json\n{json.dumps(history, indent=4)}\n```\n\n"

                res += "If the previous commands are enough to provide a satisfactory answer, go ahead and answer them in the \"reply\" section of your JSON response.\n"
                res += "Otherwise, leave the reply section empty in the JSON reply, and fill the \"commands\" array instead with commands that might help them out further.\n"
                res += "You can even suggest commands which look for files, etc... in order to look around and discover the environment further\n"
                res += "Try to avoid running the same command more than twice. Especially if it appears to have failed in the command history above, it might just mean the command requires privileges or the task is impossible. In that case, try to suggest workaround commands, OR, if it's really impossible let them know in your 'reply' section.\n"

            res += "\n## Info about our human\n"
            res += " - The terminal they will use to run the command(s): CMD on Windows\n"
            res += "\n"

            res += "## Your reply style (IMPORTANT)\n"
            res += " - Always output a parsable JSON string\n"
            res += " - Never ask follow up questions\n"
            res += "\n"

            res += "## Your skills\n"
            res += " - You are in an /c/EnvSync directory"
            res += " - You can look for files using the fd.exe in /c/EnvSync/bin/fd/fd.exe | example: fd.exe flight G: (NEVER use other methods to find files)"
            res += " - You can open a file by running python /c/EnvSync/src/utils/start.py <file_path>"
            res += "\n"

            return res

    def __init__(self, model: Model, verbose: bool = False):
        self.model: Model = model
        self.verbose: bool = verbose
        self.workingDir: str = os.getcwd()

        print(f'[ AI ] Using model: {self.model.name}')
        assert self.model.isAvailable, f"Model '{self.model.name}' is not available, cannot create Agent."

    def runCommand(self, command: str) -> CompletedProcess:

        print(f"[ RUN]: {command}", file=sys.stderr, end=' ', flush=True)

        impact = CommandImpact.measure(command)

        if (impact > CommandImpact.Minimal) and (not input("Continue? (y/n): ").strip().lower() == "y"):

            print( "\033[91m[CNCL]\033[0m Command refused", file=sys.stderr, flush=True)
            return CompletedProcess(command, -1, 'Refused to run by human')

        res: CompletedProcess = cli.runCommand(command, muteOutput=True, workingDir=self.workingDir)

        message: str = "\033[92m[ OK ]\033[0m" if res.returncode == 0 else "\033[91m[ ERR]\033[0m"
        print(message, file=sys.stderr, flush=True)

        return res

    def ask(self, queryMessage: str) -> str:
        query = IterativeAgent.Query(queryMessage)

        while True:
            print(f"Thinking...", file=sys.stderr, end='\r', flush=True)
            
            # Use Pydantic schema for structured output
            modelResponse: str = self.model.run(query.toString(), response_format=AgentResponse.model_json_schema())
            
            modelResponse = '\n'.join(line for line in modelResponse.splitlines() if not line.count('```'))
            response = AgentResponse.model_validate_json(modelResponse)

            if not response.commands:
                assert response.reply is not None, f"Model '{self.model.name}' did not provide any commands to run, and did not provide a reply either. This is an invalid response."
                return response.reply

            for command in response.commands:
                res: CompletedProcess = IterativeAgent.runCommand(self, command)
                query.previouslyRunCommands.append(res)

            continue

        return None

if __name__ == '__main__':
    pass