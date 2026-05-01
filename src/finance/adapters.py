
import os, sys
import shutil

import pdfplumber
import pandas
import datetime

from finance.Transaction import Transaction
from helpers import parseDate, parseFloat

def transactionsFromBankAudiPDF(pdfPath: str, cacheAfterParsingPath: str = None) -> list[Transaction]:

    print(f'Parsing Bank Audi {os.path.basename(pdfPath)}', end=' ', flush=True, file=sys.stderr)

    data: list[list[str]] = []
    with pdfplumber.open(pdfPath) as pdf:

        for page in pdf.pages:
            tables = page.extract_tables()

            for table in tables:
                data.extend(table)

    # remove newlines from cells
    for i, row in enumerate(data):
        data[i] = list(map(lambda cell: cell.replace('\n', ' ') if cell else None, row))

    # only keep transaction rows
    firstTransactionIndex = 0
    for i, row in enumerate(data):
        if any(map(lambda cell : cell.lower().count('transaction') if cell else False, row)):
            firstTransactionIndex = i
            break

    data = data[firstTransactionIndex:]

    dataFrame: pandas.DataFrame = pandas.DataFrame(data[1:], columns=data[0])
    
    dataFrame.drop(columns=['Long Description'], inplace=True)

    # Some rows will have half of their values on the next page on the pdf
    for i, row in dataFrame.iterrows():
        if all(row): # skip full row
            continue

        for j in range(len(row)):
            if row.iloc[j] == None:
                continue

            dataFrame.iloc[i-1, j] = dataFrame.iloc[i-1, j] + row.iloc[j] # join with the row above, in the row above
            row.iloc[j] = None # to make the whole row None

    # drop empty
    dataFrame.dropna(how='all', inplace=True)

    transactions: list[Transaction] = []
    for _, row in dataFrame.iterrows():

        t = Transaction()

        t.uniqueId = row['Serial Number'].replace(' ', '')
        t.uniqueId = int(t.uniqueId)

        t.date = parseDate(row['Transaction Date'])
        t.description = str(row['Description'])

        t.credit = parseFloat(row['Credit'])

        if t.credit == 0:
            t.credit = -1 * parseFloat(row['Debit'])

        t.balance = parseFloat(row['Running Balance'])

        t.guessAndFillType()
        transactions.append(t)

    print(f'Parsed {len(transactions)} transactions.', flush=True, file=sys.stderr)

    if cacheAfterParsingPath:

        shutil.copy(pdfPath, cacheAfterParsingPath)

        os.remove(pdfPath)
        with open(pdfPath, 'wb') as f:
            pass # create empty pdf

    return transactions

def transactionsFromRevolutCSV(csvFilePath: str) -> list[Transaction]:

    print(f'Parsing Revolut {os.path.basename(csvFilePath)}', end=' ', flush=True, file=sys.stderr)

    dataFrame: pandas.DataFrame = pandas.read_csv(csvFilePath)
    transactions: list[Transaction] = []

    for _, row in dataFrame.iterrows():

        knownStates = ['COMPLETED', 'PENDING', 'REVERTED']
        if row['State'] not in knownStates:
            print(f'[WARN] unknown revolut transaction state: {row["State"]}', flush=True, file=sys.stderr)
            continue

        t = Transaction(currency=row['Currency'])

        t.description = row['Description']

        revolutDateFormat: str = '%Y-%m-%d %H:%M:%S'
        initialDate: str = row['Started Date'] # example: 8/13/2025 11:12

        t.date = parseDate(initialDate, revolutDateFormat)
        time = datetime.datetime.strptime(initialDate, revolutDateFormat)
        t.uniqueId = int(time.timestamp())

        t.credit = parseFloat(row['Amount'])

        if row['State'] == 'REVERTED':
            t.credit = abs(t.credit)

        t.feeAmount = parseFloat(row['Fee'])
        t.balance = parseFloat(row['Balance'])

        t.guessAndFillType()
        t.convertStringAttributes()

        transactions.append(t)

    print(f'Parsed {len(transactions)} transactions.', flush=True, file=sys.stderr)
    return transactions