
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
            res += "then reply in a very specific RAW json format (without the backticks ```json stuff, just RAW json):\n"
            res += createJsonExample()
            res += "\n\n"

            if len(self.previouslyRunCommands) > 0:
                res += "They have already run some commands on their machine, here are their outputs:\n"
                history = [
                    completedProcessToDict(proc)
                    for proc in self.previouslyRunCommands
                ]
                res += f"```json\n{json.dumps(history, indent=4)}\n```\n\n"

            if len(self.previouslyRunCommands) > 0:
                res += "If you think these commands and their output is enough to answer them, go ahead and answer them with a short and consice answer in the \"reply\" section of you JSON response.\n"
                res += "Otherwise, leave the reply section empty in the JSON reply, and fill the \"commands\" array instead with commands that might help them out further.\n\n"

            res += "## Info about our human\n"
            res += " - The terminal they will use to run the command(s): GitBash on Windows\n\n"

            res += "## Your reply style (IMPORTANT)\n"
            res += " - Always output a parsable JSON string\n"

            # Write the results to query.md and overwrite it at each run
            query_path = os.path.join(CURRENT_DIR, "query.md")
            try:
                with open(query_path, "w", encoding="utf-8") as f:
                    f.write(res)
            except Exception as e:
                print(f"Warning: Could not write to {query_path}: {e}")

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
            
            data: dict = json.loads(jsonString)
            response = IterativeAgent.Response()
            response.reply = data.get("reply", None)
            response.commands = data.get("commands", [])
            return response

    def __init__(self, model: Model, verbose: bool = False):

        self.model: Model = model
        self.verbose: bool = verbose
        assert self.model.isAvailable, f"Model '{self.model.name}' is not available, cannot create Agent."

    def ask(self, queryMessage: str) -> str:

        query = IterativeAgent.Query(queryMessage)

        while True:

            modelResponse: str = self.model.run(query.toString())
            response = IterativeAgent.Response.fromJson(modelResponse)

            if not response.commands:
                assert response.reply is not None, f"Model '{self.model.name}' did not provide any commands to run, and did not provide a reply either. This is an invalid response."
                return response.reply

            # handle commands
            if not response.commands or len(response.commands) == 0:
                raise ValueError(f"Model '{self.model.name}' did not provide any commands to run, and did not provide a reply either. This is an invalid response.")

            for command in response.commands:

                res: CompletedProcess = cli.runCommand(command)
                query.previouslyRunCommands.append(res)

                continue

            continue

        return None

if __name__ == '__main__':
    pass