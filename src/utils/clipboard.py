
import pyperclip
import argparse
import sys, os

def printPasteContent() -> int:

    pasteContent: str = pyperclip.paste().strip('\n')
    if not pasteContent:
        print('Nothing in clipboard', file=sys.stderr)
        return 1

    try:
        print(pasteContent, end='', file=sys.stdout)

    finally: # avoid BrokenPipeError
        return 0

def copyFileContent(filePath: str):

    fileContent: str = ''
    with open(filePath, 'r', encoding='utf-8') as f:
        fileContent: str = f.read()

    pyperclip.copy(fileContent)
    print(f'Copied {len(fileContent.splitlines())} lines.', file=sys.stderr)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Clipboard Helper')

    option = parser.add_mutually_exclusive_group(required=True)
    option.add_argument('--copy', nargs='?', const='stdin', type=str, help='Copy stdin or file content')
    option.add_argument('--paste', action='store_true', help='Paste to stdout')

    args = parser.parse_args()

    if args.paste:
        returnCode: int = printPasteContent()
        exit(returnCode)

    if args.copy == 'stdin':
        stdinContent: str = sys.stdin.read()
        pyperclip.copy(stdinContent)
        print(f'Copied {len(stdinContent.splitlines())} lines.', file=sys.stderr)
        exit(0)

    filePath: str = args.copy
    if not os.path.isfile(filePath):
        print(f'File not found: {filePath}', file=sys.stderr)
        exit(1)

    copyFileContent(filePath)
    exit(0)