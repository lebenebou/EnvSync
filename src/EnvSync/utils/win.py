
import pyautogui
import time

import argparse
import sys

def openTaskbarApp(number: int):

    pyautogui.keyDown("win")
    pyautogui.press(str(number))
    pyautogui.keyUp("win")

# User Settings
TERMINAL_TASKBAR_NUMBER = 2

def refocusTerminal():
    openTaskbarApp(TERMINAL_TASKBAR_NUMBER)

def closeApp():
    pyautogui.hotkey("alt", "f4")

if __name__=="__main__":

    parser = argparse.ArgumentParser(description="Perform action on taskbar apps")

    parser.add_argument("taskbar_number", type=int, help="Taskbar number to open")
    parser.add_argument("-w", "--wait", action="store_true", help="Do task in background")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-k", "--kill", action="store_true", help="Close app and refocus terminal")
    group.add_argument("-r", "--restart", action="store_true", help="Restart app")

    args = parser.parse_args()

    if args.taskbar_number < 0 or args.taskbar_number > 9:
        print("Invalid taskbar app number", file=sys.stderr)
        exit(1)

    # SCRIPT START #

    if True:
        openTaskbarApp(args.taskbar_number)

    if args.kill or args.restart:
        time.sleep(0.1)
        closeApp()

    if args.restart:
        time.sleep(2)
        openTaskbarApp(args.taskbar_number)

    if args.kill or args.wait:
        refocusTerminal()
