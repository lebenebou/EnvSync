
from typing import Callable
import sys

class Color:

    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'

def printColored(text: str, color: Color, file = sys.stdout):

    RESET_CODE = '\033[0m'
    print(f'{color}{text}{RESET_CODE}', file=file)
    file.flush()

class EnvSyncTest:

    def __init__(self, name: str):

        self.name: str = name
        self.callback: Callable[..., bool] = None

    def asserts(self, functionCall: Callable[..., bool]):

        assert self.callback is None, "EnvSyncTest callback function already set!"
        self.callback = functionCall
        return self

    def execute(self) -> bool:

        print(f'[ RUN] {self.name}', file=sys.stderr)
        sys.stderr.flush()
        success: bool = self.callback()

        if success:
            printColored(f'[ OK ] {self.name}', Color.GREEN, file=sys.stderr)

        else:
            printColored(f'[FAIL] {self.name}', Color.RED, file=sys.stderr)

        sys.stderr.flush()
        return success

    @staticmethod
    def runTests(tests: list['EnvSyncTest']) -> bool:

        allSuccessful: bool = True

        for test in tests:
            print(end='\n', file=sys.stderr)
            success: bool = test.execute()
            allSuccessful = allSuccessful and success

        return allSuccessful