
import os
import shutil

def zipFolder(folderPath: str, outputZipPath: str):

    assert os.path.isdir(folderPath), f'Cannot zip folder that does not exist: {folderPath}'

    baseName = os.path.splitext(outputZipPath)[0]
    shutil.make_archive(baseName, 'zip', folderPath)

    return

def unzipFile(zipFilePath: str, extractionPath: str):

    assert os.path.isfile(zipFilePath), f'Cannot unzip file that does not exist: {zipFilePath}'
    assert zipFilePath.endswith('.zip'), f'Not a zip file: {zipFilePath}'

    zipFolderName = os.path.basename(zipFilePath).split('.zip')[0]

    shutil.unpack_archive(zipFilePath, os.path.join(extractionPath, zipFolderName))
    return