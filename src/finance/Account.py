
import os, sys

import pandas
import datetime

from GlobalEnv import GlobalEnv
from helpers import percentageDifference
from utils.stringcompare import compareStrings

from Transaction import Transaction

class Account:

    def __init__(self, name: str, currency: str, transactions: list[Transaction], maxPercentageFee: int = 15, similarityConfidance: int = 60):

        if GlobalEnv().loggingEnabled:
            print(f'Creating account... ({name} in {currency} - ', end='', flush=True, file=sys.stderr)

        self.name: str = name

        self.maxPercentageFee: int = maxPercentageFee
        self.similarityConfidance: int = similarityConfidance

        assert len(transactions) >= 0, '\nAccount must have at least one transaction'

        self.transactions = list(transactions)

        self.currency = currency
        self.convertToCurrency(self.currency)

        self.sortByDate()

        if GlobalEnv().loggingEnabled:
            print(f'{len(self.transactions)} transactions)', flush=True, file=sys.stderr)

    # hash operator for the set
    def __hash__(self):
        return hash((self.name.lower(), self.currency.lower()))

    # equal operator for the set
    def __eq__(self, other):

        if not isinstance(other, Account):
            return False

        # compare hashes
        return hash(self) == hash(other)

    def sortByDate(self, newestFirst: bool = True):
        self.transactions.sort(reverse=newestFirst)

    def convertToCurrency(self, targetCurrency: str):
        [t.convertToCurrency(targetCurrency) for t in self.transactions]

    def toDataFrame(self) -> pandas.DataFrame:

        print(f'Converting account to dataframe...', flush=True, file=sys.stderr)

        data: list[pandas.DataFrame] = []
        for t in self.transactions:
            t.account = self.name
            data.append(t.toDataFrameRow())

        return pandas.DataFrame(data)

    def _findInitialTransaction(self, start: int) -> int:

        refTransaction = self.transactions[start]

        for i in range(start, len(self.transactions)):
            candidate = self.transactions[i]

            if candidate.credit + refTransaction.credit != 0:
                continue

            descriptionSimilarity: int = compareStrings(candidate.description, refTransaction.description)
            if  descriptionSimilarity < self.similarityConfidance:
                continue

            return i

        return -1

    def _findTransactionWithFee(self, start: int) -> int:

        refTransaction = self.transactions[start]

        for i in range(start-1, -1, -1):
            candidate = self.transactions[i]

            if abs(candidate.credit) <= abs(refTransaction.credit):
                continue

            if percentageDifference(abs(refTransaction.credit), abs(candidate.credit)) > self.maxPercentageFee:
                continue

            if compareStrings(candidate.description, refTransaction.description) < self.similarityConfidance:
                continue

            return i

        return -1

    def normalizeTransactionsWithFees(self):

        toRemove: set[int] = set()

        for i, t in enumerate(self.transactions):

            if t.credit <= 0:
                continue

            initialTransactionIndex = self._findInitialTransaction(start=i)
            if initialTransactionIndex == -1:
                continue

            transactionWithFeeIndex = self._findTransactionWithFee(start=i)
            if transactionWithFeeIndex == -1:
                continue

            transactionWithFee: Transaction = self.transactions[transactionWithFeeIndex]
            transactionWithFee.feePercentage = percentageDifference(abs(t.credit), abs(transactionWithFee.credit))
            transactionWithFee.feeAmount = abs(t.credit) - abs(transactionWithFee.credit)

            toRemove.add(initialTransactionIndex)
            toRemove.add(i)

        for index in sorted(toRemove, reverse=True):
            self.transactions.pop(index)

    def addTotal(self):
        
        if len(self.transactions) == 0:
            return

        total = Transaction(self.transactions[0].currency)
        total.balance = str()
        total.description = 'TOTAL'
        total.type = str('TOTAL')

        for t in self.transactions:
            total.credit += t.credit
            total.feeAmount += t.feeAmount

        self.transactions.append(total)

def cacheAccount(account: Account):

    print(f'Caching {account.name} account with {len(account.transactions)} transactions...', end=' ', flush=True, file=sys.stderr)

    if len(account.transactions) == 0:
        print('0 transactions to cache.', flush=True, file=sys.stderr)
        return

    # bank_audi.csv
    fileName: str = account.name.lower().replace(' ', '_')
    fileName += '.csv'

    from finance.main import CACHE_DIR
    csvFilePath = os.path.join(CACHE_DIR, fileName)
    if os.path.exists(csvFilePath):
        os.remove(csvFilePath)

    print(f'(to {csvFilePath})', flush=True, file=sys.stderr)
    dataFrame = account.toDataFrame()
    dataFrame.to_csv(csvFilePath, index=False)
