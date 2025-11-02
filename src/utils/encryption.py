
import os
import sys
import subprocess

def encryptFile(inputFile: str, outputFile: str, passphrase: str):

    assert passphrase, 'Encryption passphrase cannot be empty'
    assert os.path.isfile(inputFile), f'Cannot ecnrypt file that does not exist: {inputFile}'

    command = f'openssl enc -aes-256-cbc -pbkdf2 -in {inputFile} -out {outputFile} -pass pass:{passphrase}'
    result = subprocess.run(command.split())

    if result.returncode != 0:
        print(f'[ERROR] Failed to encrypt file: {inputFile}', file=sys.stderr)
        return

    return

def decryptFile(inputFile: str, outputFile: str, passphrase: str) -> int:

    assert os.path.isfile(inputFile), f'Cannot decrypt file that does not exist: {inputFile}'

    command = f'openssl enc -d -aes-256-cbc -pbkdf2 -in {inputFile} -out {outputFile} -pass pass:{passphrase}'
    result = subprocess.run(command.split())

    if result.returncode != 0:
        print(f'[ERROR] Failed to decrypt file: {inputFile}', file=sys.stderr)
        return result.returncode
    
    return 0