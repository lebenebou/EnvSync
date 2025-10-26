
from __future__ import annotations
from EnvSync.config.ConfigFile import *

import re
import os
import sys

from EnvSync.utils import aspath
from EnvSync import EnvValues

class Variable(ConfigOption):

    def __init__(self, value: str | Exec):

        super().__init__()
        self.isCommandOutput: bool = False
        self.name: str = None

        if isinstance(value, Exec):
            self.value: str = value.toString()
            self.isCommandOutput = True
        else:
            self.value: str = value

    def asCommandOutput(self):

        assert not self.isCommandOutput, "Variable is already a command output"
        self.isCommandOutput = True
        return self

    def withName(self, name: str):
        self.name = name
        return self

    def toString(self) -> str:

        if self.isCommandOutput:
            self.value = '$(' + self.value + ')'

        return f'{self.name}="{self.value}"'

class Path(Variable):

    def __init__(self, fileOrFolder: str):

        super().__init__(fileOrFolder)

        self.value = fileOrFolder
        self.name: str = None
        self.hasBeenGivenAlternate: bool = False
        self.isSharedOnGoogleDrive: bool = False

    def slash(self, otherPath):
        otherPath = Path(otherPath)
        return Path(os.path.join(self.value, otherPath.value)).withScope(self.scope)

    def asGoogleShared(self):

        assert not self.hasBeenGivenAlternate, "This folder has been given an alternate path, it cannot be shared on google drive"
        self.withScope(ConfigOption.COMMON)

        if not CURRENT_SCOPE == ConfigOption.LAPTOP:
            self.value = os.path.join(EnvValues.G_PAVILION_15, os.path.basename(self.value))

        return self

    def withAlternateValueForScope(self, scope, alternateValue: str | Path):

        assert not self.isSharedOnGoogleDrive, "This folder is shared on google drive, it cannot be given an alternate path"

        if CURRENT_SCOPE == scope:
            self.value = alternateValue.value if isinstance(alternateValue, Path) else alternateValue

        return self

    def toLinuxPath(self) -> str:
        # this function does not wrap the path with " quotes
        if not self.value:
            return ''

        return aspath.aslinuxPath(self.value, False)

    # override
    def toString(self) -> str:

        assert self.value, f"Path doesn't have value"
        assert self.name, f"Path doesn't have name: {self.value}"

        # assert os.path.exists(self.value), f"Path doesn't exist: {self.value}"
        if not os.path.exists(self.value):
            self.withComment('[WARNING] THIS PATH DOESNT EXIST')

        self.value = self.toLinuxPath()
        return super().toString()

class Exec(ConfigOption):

    def __init__(self, initialCommand: str | Path, aliasName: str = None):

        super().__init__()

        self.args: list[str] = []
        self.aliasName = aliasName

        if not initialCommand:
            return

        self.addCommand(initialCommand)

    def addCommand(self, command: str | Path | Exec):

        if isinstance(command, Path):
            command = command.value

        if isinstance(command, Exec):
            return self.addArgs(command.args)

        if isinstance(command, Function):
            return self.addArg(command.name)

        # command is str...

        if os.path.exists(command):
            self.addPath(command)
        else:
            self.addArg(command)

        return self

    def addArg(self, arg: str):
        arg = arg.strip()
        self.args.append(arg)
        return self

    def addExecOutput(self, command: Exec):
        return self.addArg(f'$({command.toString()})')

    def addQuoted(self, arg: str):

        arg = arg.strip('"')
        arg = arg.strip("'")

        arg = r"'\''" + arg
        arg = arg + r"'\''"

        return self.addArg(arg)

    def addArgs(self, args: list[str]):
        self.args.extend(args)
        return self

    def andThen(self, command: str):
        self.addArg('&&')
        return self.addCommand(command)

    def then(self, command: str):
        self.addArg(';')
        return self.addCommand(command)

    def ifFailed(self, command: str):
        self.addArg('||')
        return self.addCommand(command)


    def delay(self, seconds: int):
        return self.andThen(f'sleep {seconds}')

    def tee(self, command: str | Path = None):
        
        self.pipe('tee')
        self.addArg(f'>({command})')
        return self

    def inParallel(self, command: str | Path = None):

        while self.args and self.args[-1] == '&':
            self.args.pop()

        self.addArg('&')
        return self.addCommand(command) if command else self

    def disown(self):
        self.inParallel()
        return self.addArg('disown')

    def muteOutput(self, std: int = 3):

        assert std in [1, 2, 3]

        if std == 3:
            std = '&'

        return self.addArg(f'{std}> /dev/null')

    def addPath(self, p: Path | str):

        if isinstance(p, str): # overload function
            p = Path(p.strip())

        self.withScope(p.scope)

        linuxPath = p.toLinuxPath()
        if ' ' in linuxPath:
            linuxPath = '"' + linuxPath + '"'

        return self.addArg(linuxPath)

    def pipe(self, command: str | Exec):
        self.addArg('|')
        return self.addCommand(command)

    def grep(self, pattern: str):
        self.pipe('grep')
        self.addArg('-E')
        return self.addArg(pattern)

    # override
    def toString(self) -> str:

        if not self.aliasName:
            return " ".join(self.args)

        line = f"alias {self.aliasName}='"
        line += " ".join(self.args)
        line += "'"
        return line

class Alias(ConfigOption):

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def to(self, exec: Exec | str) -> Exec:

        assert self.name, f'Name not specified for alias'

        if isinstance(exec, Path):
            exec = Exec(exec.value)

        if isinstance(exec, str) or isinstance(exec, Exec):
            exec = Exec(exec) # deep copy the exec

        self.scope = exec.scope
        exec.aliasName = self.name
        return exec

    # override
    def toString(self) -> str:
        raise NotImplementedError("Alias doesn't override toString() method, please bind to() an Exec")

class Function(ConfigOption):

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.executionLines: list[Exec] = []

    def addExecLine(self, exec: Exec | str):

        assert self.name, f'Name not specified for function'

        if isinstance(exec, str):
            exec = Exec(exec)

        self.executionLines.append(exec)
        return self
        
    def thenExecute(self, lines: list[Exec] | Exec | str):

        if isinstance(lines, str):
            return self.thenExecute([Exec(lines)])

        if isinstance(lines, Exec):
            return self.thenExecute([lines])

        assert isinstance(lines, list), 'Line isnt an Exec list type'

        for line in lines:
            self.addExecLine(line)

        return self

    # override
    def toString(self) -> str:

        res = f'{self.name}()\n'
        res += '{\n'

        for execLine in self.executionLines:
            res += f'\t{execLine.toString()}\n'

        res += '}\n'
        return res

class cdInto(Exec):

    def __init__(self, dir: Path | str):

        super().__init__('cd')
        self.addCommand(dir)
        self.tag = 'Directory Shortcuts'

class RunPython(Exec):

    def __init__(self, scriptPath: Path | str):

        super().__init__('python')
        self.addCommand(scriptPath)
        self.tag = 'Python scripts'

class InlinePython(RunPython):

    def __init__(self, runImmediately = False):
        super().__init__('-c')
        self.runImmediately = runImmediately

    def linesAre(self, lines: list[str]):

        if self.runImmediately:
            return self.addArg("'" + '; '.join(lines) + "'")
        else:
            return self.addQuoted('; '.join(lines))

class BashProfile(ConfigFile):

    def __init__(self):
        super().__init__()

    # override
    def commentChar(self) -> chr:
        return '#'

def runUnitTests():

    # Python
    current_file = os.path.abspath(__file__)
    assert RunPython(current_file).toString().__eq__(f'python {aspath.aslinuxPath(current_file)}')

    # Alias
    aliasRegexPattern = r'alias\s+\w+=["\'].*["\']'
    assert re.match(aliasRegexPattern, Alias('aliasName').to(RunPython('script.py')).toString())
    assert re.match(aliasRegexPattern, Alias('aliasName').to(cdInto('D:\\')).toString())

if __name__ == "__main__":

    # Run tests
    print("Running unit tests...", file=sys.stderr)
    runUnitTests()
    print("All tests passed.", file=sys.stderr)