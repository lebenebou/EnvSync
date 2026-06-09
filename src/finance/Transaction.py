
import sys

import datetime
import pandas
from enum import Enum, auto

from finance.helpers import parseDate, parseFloat

import unicodedata

import re

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

class TransactionType(Enum):
    other = auto()
    food = auto()
    concert = auto()
    entertainment = auto()
    cinema = auto()
    software = auto()
    gym = auto()
    mobile = auto()
    music = auto()
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

        TransactionType.service:
            [
                "poste"
            ],

        TransactionType.cinema:
            [
             "pathe",
             "grand rex",
             "cinema",
             "max linder",
            ],

        TransactionType.entertainment:
            [
             "billard",
             "ping pang",
             "disney",
            ],

        TransactionType.concert:
            [
             "grand mix",
             "tonic walter",
             "shotgun",
             "weezevent",
             "billet",
             "ticket",
             "viagogo",
            ],

        TransactionType.software:
            [
             "spotify",
             "apple",
             "itunes",
             "fouadraheb",
             "playstation",
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
             "esim",
             "simly",
             "sfr",
             "orange",
             "genvoice",
             "alfa",
             "connect",
            ],

        TransactionType.music:
            [
             "c.o.m",
             "woodbrass",
            ],

        TransactionType.pharmacy:
            [
             "pharm",
            ],

        TransactionType.groceries:
            [
             "market",
             "relay",
             "marche",
             "superm",
             "carrefour",
             "normal",
             "franprix",
             "monop",
             "alimentat",
             "bcf",
             "7-eleven",
             "walmart",
             "oxxo",
            ],

        TransactionType.shopping:
            [
             "uniqlo",
             "outlet",
             "tweeter",
             "nordstrom",
             "amazon",
             "zara",
             "decathlon",
             "fnac",
            ],

        TransactionType.transport:
            [
             "transport",
             "ratp",
             "sncf",
             "uber",
             "taxi",
             "bolt",
             "lime",
             "ilevia",
             "metro",
            ],

        TransactionType.travel:
            [
             "mea ",
             "middle east airlines",
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
             "hotel",
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
             "exchange",
             "trsf",
             "cardpay",
             "internal",
             "top-up",
             "ghadi",
             "card",
             "payment",
            ],

        TransactionType.food:
            [
             "coffee",
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

    def __init__(self, currency = 'USD'):

        self.account: str = None
        self.uniqueId: int = -1

        self.description: str = None
        self.date: datetime.date = None

        self.type = TransactionType.other

        self.credit: float = 0.
        self.feePercentage: float = 0.
        self.feeAmount: float = 0.

        self.balance: float = 0.
        self.currency: str = currency

    # Comparator
    def __lt__(self, other: 'Transaction') -> bool:

        if self.date != other.date:
            return self.date < other.date

        return self.uniqueId < other.uniqueId

    def prepareForPrettyPrint(self):

        self.__delattr__('uniqueId')
        self.__delattr__('feePercentage')

        # Make date readable as in (3 Jan 2024)
        if self.date:
            self.date = self.date.strftime('%d %b %Y')

         # Strip description to 40 characters
        if len(self.description) > 40:
            self.description = self.description[:37] + '...'

    def convertStringAttributes(self): # convert string attributes to their correct types, if possible

        for attrName, attrValue in self.__dict__.items():
            self.__setattr__(attrName, str(attrValue)) # convert all to str first

        for attrName, attrValue in self.__dict__.items():
            try:
                self.__setattr__(attrName, parseFloat(attrValue)) # try to convert to float, if possible
            except ValueError:
                pass

        self.uniqueId = int(self.uniqueId)

        if self.type not in TransactionType.__members__:
            print(f'[WARN] Transaction type: {self.type} not found in TransactionType enum. Defaulting to "other".', file=sys.stderr)
            self.type = 'other'

        self.type = TransactionType[self.type] # string to enum

        if isinstance(self.date, str):
            self.date = parseDate(self.date, dateFormat='%Y-%m-%d')

    def toDataFrameRow(self) -> dict:

        self.convertStringAttributes()
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

        t.convertStringAttributes()
        t.guessAndFillType()

        return t

    def convertToCurrency(self, targetCurrency: str):

        if self.currency == targetCurrency:
            return

        rate = Currency.getRate(self.currency, targetCurrency)

        self.credit *= rate
        self.feeAmount *= rate
        self.balance *= rate

        self.currency = targetCurrency

    def cleanDescription(self):

        if not isinstance(self.description, str) or not self.description:
            self.description = "No Description"
            return

        regexToRemove = ['branch', 'pos', 'prch', 'cash', 'onsite', 'offsite', 'mpfx', r'm\S*8831\S*', r'[^\w]{2,}', '^-', r'\b\d+\b']
        for w in regexToRemove:
            self.description = re.sub(w, ' ', self.description, flags=re.IGNORECASE)

        self.description = re.sub(r'\s+', ' ', self.description).strip()

        def removeAccents(inputStr: str) -> str:
            return ''.join(
                c for c in unicodedata.normalize('NFD', inputStr) if unicodedata.category(c) != 'Mn'
            )

        self.description = removeAccents(self.description)

        # capitalize first letter of each word, lowercase the rest
        self.description = ' '.join(word.capitalize() for word in self.description.split())

    def guessAndFillType(self) -> TransactionType:

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
        return bestGuess

    def matchesFilter(self, filter: 'TransactionFilter') -> bool:

        assert isinstance(filter, TransactionFilter), f'filter must be of type TransactionFilter, got {type(filter)}'

        if filter is None or filter.isEmpty():
            return True

        attributesToCompare = ['account', 'description', 'type', 'date']
        match: bool = True

        for attr in attributesToCompare:

            filterValue = filter.__dict__[attr]
            if filterValue == None:
                continue

            transactionValue = self.__dict__[attr]
            if transactionValue == None:
                return False

            if not isinstance(transactionValue, str):
                match &= (transactionValue == filterValue)

            if isinstance(transactionValue, str):
                match &= (filterValue.lower() in transactionValue.lower())

            if not match:
                return False

        # Dates
        if filter.dateLowerBound and self.date < filter.dateLowerBound:
            return False

        if filter.dateUpperBound and self.date > filter.dateUpperBound:
            return False

        # Exclude term
        fullString: str = ' - '.join([
                                    self.account,
                                    self.description,
                                    self.type.name
                                      ]).lower()

        if filter.excludeRegex is not None and re.search(filter.excludeRegex, fullString):
            return False

        return True

class TransactionFilter(Transaction):

    MinDate = datetime.datetime.strptime('01-01-1900', "%d-%m-%Y").date()
    MaxDate = datetime.datetime.strptime('01-01-2099', "%d-%m-%Y").date()

    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):

        for attr in self.__dict__.keys():
            self.__dict__[attr] = None

        self.dateLowerBound = None
        self.dateUpperBound = None
        self.excludeRegex: re.Pattern = None

    def isEmpty(self) -> bool:
        return all(value is None for value in self.__dict__.values())