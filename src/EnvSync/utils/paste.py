
import pyperclip

if __name__ == '__main__':

    try:
        print(pyperclip.paste().strip('\n'), end='\n')

    finally: # BrokenPipeError
        exit(0)