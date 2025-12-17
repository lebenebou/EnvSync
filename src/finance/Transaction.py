
import sys

import datetime
import pandas
from enum import Enum, auto

from finance.helpers import parseDate, percentageDifference, parseFloat
from utils.stringcompare import compareStrings

import unicodedata

class Currency:

    _Rate = {
        'EUR USD': 1.17,
    }

    @staticmethod
    def currencySupported(currency: str) -> bool:

        for key in Currency._Rate.keys():
            if currency in key.split():
                return True

        return False
        
    @staticmethod
    def getRate(fromCurrency: str, toCurrency: str) -> float:

        if fromCurrency == toCurrency:
            return 1.
        
        key = f'{fromCurrency} {toCurrency}'
        if key in Currency._Rate:
            return Currency._Rate[key]

        key = f'{toCurrency} {fromCurrency}'
        if key in Currency._Rate:
            return 1. / Currency._Rate[key]
        
        assert False, f'Currency conversion rate from {fromCurrency} to {toCurrency} not found'

class TransactionLocation(Enum):
    lebanon = auto()
    france = auto()
    mexico = auto()

    def __str__(self) -> str:
        return self.name

class TransactionType(Enum):
    other = auto()
    food = auto()
    entertainment = auto()
    software = auto()
    gym = auto()
    mobile = auto()
    pharmacy = auto()
    groceries = auto()
    shopping = auto()
    transport = auto()
    travel = auto()
    service = auto()
    games = auto()
    hotel = auto()
    salary = auto()
    atm = auto()
    fee = auto()
    transfer = auto()

    def __str__(self) -> str:
        return self.name

class Transaction:

    Categories = [cat for cat in TransactionType.__iter__()]
    CategoryMap = {

        TransactionType.food:
            [
             "toters",
             "pepere",
             "basta",
             "pasta",
             "sandwich",
             "grill",
             "chicken",
             "poulet",
             "taco",
             "janna",
             "poke",
             "bistro",
             "restaurant",
             "eats",
             "cafe",
             "coffee",
            ],

        TransactionType.service:
            [
                "poste"
            ],

        TransactionType.entertainment:
            [
             "pathe",
             "grand rex",
             "grand mix",
             "tonic walter",
             "shotgun",
             "phantom",
             "billard",
             "disney",
             "cinema",
             "weezevent",
             "play",
             "billet",
             "ticket",
             "viagogo",
            ],

        TransactionType.software:
            [
             "spotify",
             "apple",
             "fouadraheb",
            ],

        TransactionType.gym:
            [
             "gym",
             "fit",
             "neoness",
            ],

        TransactionType.mobile:
            [
             "mobile",
             "simly",
             "sfr",
             "orange",
             "genvoice",
             "alfa",
            ],

        TransactionType.pharmacy:
            [
             "pharm",
            ],

        TransactionType.groceries:
            [
             "market",
             "marche",
             "superm",
             "carrefour",
             "normal",
             "franprix",
             "monop",
             "alimentat",
             "bcf",
             "7-eleven",
             "oxxo",
            ],

        TransactionType.shopping:
            [
             "uniqlo",
             "outlet",
             "amazon",
             "zara",
             "decathlon",
            ],

        TransactionType.transport:
            [
             "ratp",
             "sncf",
             "uber",
             "bolt",
             "lime",
             "ilevia",
             "metro",
            ],

        TransactionType.travel:
            [
             "mea ",
             "air france",
             "airfrance",
            ],

        TransactionType.games:
            [
             "steam",
            ],

        TransactionType.hotel:
            [
             "meridien",
            ],

        TransactionType.salary:
            [
             "salary",
             "salari",
             "salaire",
            ],

        TransactionType.atm:
            [
             "atm",
             "withdrawal",
             "cash",
            ],

        TransactionType.transfer:
            [
             "transfer",
             "trsf",
             "cardpay",
             "internal",
             "top-up",
             "ghadi",
             "card",
             "payment",
            ],

        TransactionType.fee:
            [
             "fee",
             "charge",
             "interest",
             "credit",
             "aol",
            ],

    }

    def __init__(self, currency = 'USD', accountName: str = None):

        self.uniqueId: int = -1
        self.accountName: str = accountName

        self.description: str = None
        self.date: datetime.date = None

        self.type = TransactionType.other

        self.credit: float = 0.
        self.feePercentage: float = 0.
        self.feeAmount: float = 0.

        self.balance: float = 0.
        self.currency: str = currency

        self.location: TransactionLocation = None

    def correctAttributeTypes(self):

        for attrName, attrValue in self.__dict__.items():

            self.__setattr__(attrName, str(attrValue))
            try:
                if attrValue is None: print(attrName)
                self.__setattr__(attrName, parseFloat(attrValue))
            except ValueError:
                pass

        self.uniqueId = int(self.uniqueId)
        self.type = TransactionType[self.type]

        self.location = TransactionLocation[self.location]

        if isinstance(self.date, str):
            self.date = parseDate(self.date, dateFormat='%Y-%m-%d')

    def toDataFrameRow(self) -> dict:

        self.correctAttributeTypes()
        data: dict = {}
        for attrName, attr in self.__dict__.items():
            data[attrName] = str(attr)

        return data

    @staticmethod
    def fromDataFrameRow(row: pandas.Series) -> 'Transaction':

        t = Transaction()
        # iterate over the __dict__ of the transaction and set the attributes from the row
        for attrName in t.__dict__.keys():

            assert attrName in row, f'Attribute {attrName} not found in data frame row'

            value = row[attrName]
            t.__setattr__(attrName, value)
            t.__dict__[attrName] = str(value)

        try:
            t.date = parseDate(t.date, dateFormat='%Y-%m-%d')
        except ValueError:
            t.date = parseDate(t.date, dateFormat='%m/%d/%Y')

        t.correctAttributeTypes()
        t.fillTypeAndLocation()

        return t

    def convertToCurrency(self, targetCurrency: str):

        if self.currency == targetCurrency:
            return

        rate = Currency.getRate(self.currency, targetCurrency)

        self.credit *= rate
        self.feeAmount *= rate
        self.balance *= rate

        self.currency = targetCurrency

    @staticmethod
    def descriptionToLocation(description: str):

        description: str = description.lower().replace('pos', '').replace('prch', '').replace('cash', '').replace('onsite', '')

        if description.endswith('fr') or description.endswith('fra'):
            return TransactionLocation.france

        if 'ratp' in description:
            return TransactionLocation.france

        if 'pue' in description.split(' '):
            return TransactionLocation.mexico

        if 'mex' in description.split(' '):
            return TransactionLocation.mexico

        if 'mx' in description.split(' '):
            return TransactionLocation.mexico

        return TransactionLocation.lebanon

    def cleanDescription(self):

        self.description = self.description.replace('pos', '').replace('prch', '').replace('cash', '').replace('onsite', '')

        def removeAccents(inputStr: str) -> str:
            return ''.join(
                c for c in unicodedata.normalize('NFD', inputStr) if unicodedata.category(c) != 'Mn'
            )

        self.description = removeAccents(self.description)

    def fillTypeAndLocation(self) -> TransactionType:

        bestScore = 0
        bestGuess = TransactionType.food

        for category, keywords in Transaction.CategoryMap.items():

            self.cleanDescription()

            score = sum(self.description.lower().count(w) for w in keywords)
            if score <= bestScore:
                continue

            bestScore = score
            bestGuess = category

        self.type = bestGuess
        self.location = Transaction.descriptionToLocation(self.description)
        return bestGuess

class Series:

    Confidance = 60
    MaxPercentageFee = 15

    def __init__(self, currency: str, transactions: list[Transaction]):

        print(f'Creating series...', flush=True, file=sys.stderr)

        assert len(transactions) >= 2, f'Cannot create series with {len(transactions)} transaction(s)'

        self.currency = currency
        self.transactions = list(transactions)
        self.convertToCurrency(self.currency)

        self.sortByDate()
        self.normalizeTransactionsWithFees()

    def sortByDate(self, newestFirst: bool = True):
        self.transactions = list(sorted(self.transactions, key=lambda t: (t.date, t.uniqueId), reverse=newestFirst))

    def convertToCurrency(self, targetCurrency: str):
        [t.convertToCurrency(targetCurrency) for t in self.transactions]

    def extend(self, Additionaltransactions: list[Transaction]):

        [t.convertToCurrency(self.currency) for t in Additionaltransactions]

        self.transactions.extend(Additionaltransactions)
        self.sortByDate()

        n: int = len(self.transactions)
        assert n >= 2

        t0: Transaction = self.transactions[n-1]

        accounts: set[str] = set()
        accounts.add(t0.accountName)

        runningBalance: float = t0.balance

        for i in range(n-2, -1, -1):

            current: Transaction = self.transactions[i]

            if current.accountName not in accounts:
                runningBalance += current.balance
                accounts.add(current.accountName)
            else:
                runningBalance += current.credit

            current.balance = runningBalance
            self.transactions[i] = current

    def toDataFrame(self) -> pandas.DataFrame:

        print(f'Converting series to dataframe...', flush=True, file=sys.stderr)

        data: list[pandas.DataFrame] = []
        for t in self.transactions:
            data.append(t.toDataFrameRow())

        return pandas.DataFrame(data)

    def _findInitialTransaction(self, start: int) -> int:

        refTransaction = self.transactions[start]

        for i in range(start, len(self.transactions)):
            candidate = self.transactions[i]

            if candidate.credit + refTransaction.credit != 0:
                continue

            descriptionSimilarity: int = compareStrings(candidate.description, refTransaction.description)
            if  descriptionSimilarity < Series.Confidance:
                continue

            return i

        return -1

    def _findTransactionWithFee(self, start: int) -> int:

        refTransaction = self.transactions[start]

        for i in range(start-1, -1, -1):
            candidate = self.transactions[i]

            if abs(candidate.credit) <= abs(refTransaction.credit):
                continue

            if percentageDifference(abs(refTransaction.credit), abs(candidate.credit)) > Series.MaxPercentageFee:
                continue

            if compareStrings(candidate.description, refTransaction.description) < Series.Confidance:
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

    def filterByCategory(self, category: TransactionType):
        
        if isinstance(category, str): # turn the category into an enum
            category = next((catEnum for catEnum in Transaction.CategoryMap.keys() if catEnum.name == category), TransactionType.other)

        self.transactions = [t for t in self.transactions if t.type == category]

    def filterByLocation(self, location: TransactionLocation):
        
        if isinstance(location, str): # turn the category into an enum
            location = next((loc for loc in TransactionLocation.__iter__() if loc.name == location), TransactionType.other)

        self.transactions = [t for t in self.transactions if t.location == location]

    def filterBySubstring(self, filter: str):
        self.transactions = [t for t in self.transactions if filter.lower() in t.description.lower()]

    def dateFilter(self, lowerBound: datetime.date, upperBound: datetime.date):
        self.transactions = [t for t in self.transactions if t.date >= lowerBound and t.date <= upperBound]

    def addTotal(self):
        
        if len(self.transactions) == 0:
            return

        total = Transaction(self.transactions[0].currency)
        total.balance = self.transactions[0].balance
        total.description = 'TOTAL'
        total.type = str('TOTAL')

        for t in self.transactions:
            total.credit += t.credit
            total.feeAmount += t.feeAmount

        self.transactions.append(total)

    def prepareForPrettyPrint(self):

        for t in self.transactions:

            t.__delattr__('uniqueId')
            t.__delattr__('feePercentage')
            # t.feePercentage = round(t.feePercentage, 4)
