
import sys, os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from GlobalEnv import GlobalEnv, ConfigScope

class ConfigOption:

    def __init__(self):

        self.tag = None
        self.comment = None
        self.scope: ConfigScope = ConfigScope.COMMON

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