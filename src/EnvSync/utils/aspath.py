
import argparse
import sys

def aslinuxPath(path: str, wrapInQuotesIfSpaces: bool = True) -> str:

    if len(path) < 2:
        return path

    path = path.replace('\\', '/')
    path = path.replace(':', '', 1)
    path = path[0].lower() + path[1:]
    path = path if path.startswith('/') else ('/' + path)

    if wrapInQuotesIfSpaces and ' ' in path:
        return f'"{path}"'

    assert '\\' not in path, "Linux path contains backslashes"
    return path

def asWindowsPath(path: str) -> str:

    if len(path) < 2:
        return path

    if path[1] == ':':
        return path

    path = path.replace('/', '\\')
    path = path[1:]
    path = path[0].upper() + ':' + path[1:]
    return path

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Convert between windows & linux paths')

    opSystem = parser.add_mutually_exclusive_group()
    opSystem.add_argument('-windows', action='store_true', help='Convert linux to windows path')
    opSystem.add_argument('-linux', action='store_true', help='Convert windows to linux path')

    parser.add_argument('--from_stdin', action='store_true', help='read path from stdin', required=True)

    args = parser.parse_args()

    originalPath = sys.stdin.read().strip()

    if args.linux:
        print(aslinuxPath(originalPath).strip(), file=sys.stdout, end='')
        exit(0)

    if args.windows:
        print(asWindowsPath(originalPath).strip(), file=sys.stdout, end='')
        exit(0)

    parser.print_help()
    exit(1)

if __name__ == '__tests__':
# if __name__ == '__main__':

    windowsPath = 'C:\\Users\\yyamm\\Desktop\\Code\\Python\\Automations\\Bash\\aspath.py'
    print(windowsPath)

    linuxPath = aslinuxPath(windowsPath)
    print(linuxPath)

    windowsPath = asWindowsPath(linuxPath)
    print(windowsPath)

    print(aslinuxPath('D:'))
    print(asWindowsPath('/d'))