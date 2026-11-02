
import os, sys, json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from utils import cli
from subprocess import CompletedProcess

def createJsonExample() -> str:

    example = {
        "reply": "your_optional_reply_here (leave empty if you want to ask the human to run some commands)",
        "commands": [
            "command1",
            "command2",
            "commandx..."
        ]
    }

    return json.dumps(example, indent=4)

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
        # This method should be overridden
        # It should return True if the model is available for use, and False otherwise
        raise NotImplementedError("You must implement the check availability method in subclasses of Model")

    def run(self, queryMessage: str) -> str:
        # This method should be overridden
        # It should take a Query object and return a Response object
        raise NotImplementedError("You must implement the run method in subclasses of Model")

class IterativeAgent:

    class Query:
        def __init__(self, queryMessage: str):
            self.queryMessage: str = queryMessage
            self.previouslyRunCommands: list[CompletedProcess] = []

        def toString(self) -> str:
            # builds an .md file
            res: str = "You are about to help a human with a request, they're asking:\n"
            res += f'"{self.queryMessage}"\n\n'

            res += "If you believe that you can help them further by having them run some comamnds on their machine,\n"
            res += "then reply in a very specific RAW json format:\n"
            res += createJsonExample()
            res += "\n\n"

            if len(self.previouslyRunCommands) > 0:
                res += "They have already run some commands on their machine which can help you navigate and discover the environment, here are their outputs:\n"
                history = [
                    completedProcessToDict(proc)
                    for proc in self.previouslyRunCommands
                ]
                res += f"```json\n{json.dumps(history, indent=4)}\n```\n\n"

            if len(self.previouslyRunCommands) > 0:
                res += "If the previous commands are enough to provide a satisfactory answer (it must be satisfactory), go ahead and answer them in the \"reply\" section of your JSON response.\n"
                res += "Otherwise, leave the reply section empty in the JSON reply, and fill the \"commands\" array instead with commands that might help them out further.\n"
                res += "If the human typed a wrong command, or doesnt have privileges, try to suggest other commands as workardounds\n"
                res += "You can even suggest commands which look for files, etc... in order to look around and discover the environment further\n"
                res += "\n"

            res += "## Info about our human\n"
            res += " - The terminal they will use to run the command(s): GitBash on Windows\n\n"

            res += "## Your reply style (IMPORTANT)\n"
            res += " - Always output a parsable JSON string\n"
            res += " - Never ask follow up questions\n"

            return res

    class Response:
        def __init__(self):
            self.reply: str = None
            self.commands: list[str] = []

        @staticmethod
        def fromJson(jsonString: str) -> 'IterativeAgent.Response':

            start: int = jsonString.find('{')
            end: int = jsonString.rfind('}')

            if start != -1 and end != -1:
                jsonString = jsonString[start:end+1]
            else:
                raise ValueError(f"Invalid JSON string: {jsonString}")
            
            try:
                data: dict = json.loads(jsonString)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON string: {jsonString}. Error: {str(e)}")

            response = IterativeAgent.Response()
            response.reply = data.get("reply", None)
            response.commands = data.get("commands", [])
            return response

    def __init__(self, model: Model, verbose: bool = False):

        self.model: Model = model
        self.verbose: bool = verbose
        self.workingDir: str = os.getcwd()
        assert self.model.isAvailable, f"Model '{self.model.name}' is not available, cannot create Agent."

    def ask(self, queryMessage: str) -> str:

        query = IterativeAgent.Query(queryMessage)

        while True:

            print(f"Thinking...", file=sys.stderr, end='\r', flush=True)
            modelResponse: str = self.model.run(query.toString())
            response = IterativeAgent.Response.fromJson(modelResponse)

            if not response.commands:
                assert response.reply is not None, f"Model '{self.model.name}' did not provide any commands to run, and did not provide a reply either. This is an invalid response."
                return response.reply

            # handle commands
            if not response.commands or len(response.commands) == 0:
                raise ValueError(f"Model '{self.model.name}' did not provide any commands to run, and did not provide a reply either. This is an invalid response.")

            for command in response.commands:

                print(f"[ RUN]: {command}", file=sys.stderr, end=' ')

                res: CompletedProcess = cli.runCommand(command, muteOutput=True, workingDir=self.workingDir)
                message: str = "\033[92m[ OK ]\033[0m" if res.returncode == 0 else "\033[91m[ ERR]\033[0m"
                print(message, file=sys.stderr, flush=True)

                query.previouslyRunCommands.append(res)

                continue

            continue

        return None

if __name__ == '__main__':
    pass