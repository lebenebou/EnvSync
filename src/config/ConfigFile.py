
import sys, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from GlobalEnv import GlobalEnv, ConfigScope

class ConfigOption:

    def __init__(self):

        self.tag = None
        self.comment = None
        self.scope = ConfigScope.COMMON

    def withTag(self, tag: str):

        if not tag:
            self.tag = None
            return self

        self.tag = tag.strip().capitalize()
        return self

    def withScope(self, newScope: ConfigScope):

        if self.scope == ConfigScope.COMMON:
            self.scope = 0

        self.scope |= newScope
        return self

    def withComment(self, comment: str):

        self.comment = comment
        return self

    def toString(self) -> str:
        raise NotImplementedError("This method is virtual, please override")

class SectionFromFile(ConfigOption):

    def __init__(self, filePath: str):
        super().__init__()
        self.filePath = filePath

    # override
    def toString(self) -> str:

        bashFunctionsDir = os.path.join(GlobalEnv().repoSrcPath, 'config', 'sections')

        if not os.path.exists(self.filePath):
            self.filePath = os.path.join(bashFunctionsDir, self.filePath)

        assert os.path.exists(self.filePath), f"File does not exist: {self.filePath}"

        lines: str = None
        with open(self.filePath, 'r') as f:
            lines = f.read().split('\n')

        while len(lines) and not lines[0].strip():
            lines.pop(0)

        while len(lines) and not lines[-1].strip():
            lines.pop(-1)

        assert len(lines) > 0, f"File is empty: {self.filePath}"
        return '\n'.join(lines)

class ConfigFile:

    def __init__(self):
        self.options: list[ConfigOption] = []

    def add(self, option: ConfigOption):
        self.options.append(option)

    def commentChar(self) -> chr:
        raise NotImplementedError("This method is virtual, please override")

    def createTagOrComment(self, optionTagOrComment: str = None) -> str:

        if not optionTagOrComment:
            return ""

        return f'{self.commentChar()} {optionTagOrComment}\n'

    def toString(self, scopeFilter = GlobalEnv().currentScope):
        
        res = '\n'
        currentTag = None
        for option in (op for op in self.options if op.scope & scopeFilter):
            
            if currentTag != option.tag:

                res += "\n"
                res += self.createTagOrComment(option.tag)

                currentTag = option.tag

            res += option.toString()

            if option.comment:
                res += ' ' + self.createTagOrComment(option.comment)

            if not res.endswith("\n"):
                res += "\n"

        return res

    @staticmethod
    def writeToFile(path: str, stringStream: str):
        open(path, 'w').write(stringStream)
