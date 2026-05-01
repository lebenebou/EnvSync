
from Account import Account
from Transaction import Transaction, TransactionFilter
from datetime import datetime

class Portfolio:

    def __init__(self, currency: str):

        self.accounts: set[Account] = set()
        self.currency: str = currency

        emptyFilter = Transaction()
        for attr in emptyFilter.__dict__.keys():
            emptyFilter.__dict__[attr] = None

        self.filter: Transaction = emptyFilter

        self.dateLowerBound: datetime.date = datetime.strptime('01-01-1900', "%d-%m-%Y").date()
        self.dateUpperBound: datetime.date = datetime.strptime('01-01-2099', "%d-%m-%Y").date()

    def withAccount(self, account: Account):

        account.convertToCurrency(self.currency)
        self.accounts.add(account)
        return self

    def withFilter(self, filter: TransactionFilter):

        if filter == None:
            self.filter = TransactionFilter()
            return self

        assert type(filter).__name__ == 'TransactionFilter', f'filter must be of type TransactionFilter, got {type(filter)}'

        self.filter = filter
        return self

    def withDateLowerBound(self, dateLowerBound: datetime.date):

        if dateLowerBound == None:
            return self

        self.dateLowerBound = dateLowerBound
        return self
    
    def withDateUpperBound(self, dateUpperBound: datetime.date):

        if dateUpperBound == None:
            return self

        self.dateUpperBound = dateUpperBound
        return self

    def build(self) -> Account:
        
        transactions: list[Transaction] = []
        for account in self.accounts:
            transactions.extend(account.transactions)

        transactions.sort(reverse=True)

        portfolioAccount = Account('Portfolio', self.currency, transactions)

        if self.filter:
            portfolioAccount.transactions = [t for t in portfolioAccount.transactions if t.matchesFilter(self.filter)]

        if self.dateLowerBound:
            portfolioAccount.transactions = [t for t in portfolioAccount.transactions if t.date >= self.dateLowerBound]

        if self.dateUpperBound:
            portfolioAccount.transactions = [t for t in portfolioAccount.transactions if t.date <= self.dateUpperBound]

        return portfolioAccount