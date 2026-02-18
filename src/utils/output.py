
import re
import sys
import time
from tabulate import tabulate

def printObjectList(objects: list[object], csv: bool = False):

    if len(objects) == 0:
        return

    print(end='\n', flush=True, file=sys.stderr)

    tableContent = [obj.__dict__.values() for obj in objects]
    headers = [key.capitalize() for key in objects[0].__dict__.keys()]

    if csv:
        fullTable: str = tabulate(tableContent, headers=headers, tablefmt='tsv').replace('\t', ',')
        fullTable = re.sub(r'\s*,\s*', r',', fullTable) # remove all spaces in between commas
    else:
        fullTable: str = tabulate(tableContent, headers=headers)

    headerCutOff = 1 if csv else 2
    headerContent = '\n'.join(fullTable.split('\n')[:headerCutOff])
    tableContent = '\n'.join(fullTable.split('\n')[headerCutOff:])

    if not len(tableContent):
        return

    if not csv:
        print(headerContent, file=sys.stderr, end='\n\n') # allow the use of grep while keeping the headers
    else:
        print(headerContent, file=sys.stdout, end='\n')

    time.sleep(0.005) # this is to avoid stderr getting mixed with stdout, force headers to first line

    try:
        print(tableContent, file=sys.stdout)
    except BrokenPipeError: # some commands like "head" will close the pipe early and prevent the program from outputting more lines
        pass