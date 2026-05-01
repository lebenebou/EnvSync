
import sys, os
import argparse

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.append(PARENT_DIR)

from GlobalEnv import GlobalEnv
sys.path.append(GlobalEnv().repoSrcPath)
from utils.output import printObjectList

if GlobalEnv().accessEncryptedFiles(cmdFallback=True) != 0:
    exit(1)

ENC_FINANCE_DIR = os.path.join(GlobalEnv().encryptedPath, "finance")

REPORTS_DIR = os.path.join(ENC_FINANCE_DIR, "reports")
CACHE_DIR = os.path.join(ENC_FINANCE_DIR, "cached")

from datetime import datetime
import pandas

from finance.Transaction import Transaction, TransactionFilter, TransactionType, Currency
from finance.Account import Account, cacheAccount
from finance.Portfolio import Portfolio
from finance.adapters import transactionsFromBankAudiPDF, transactionsFromRevolutCSV

def transactionsFromCachedCsv(csvFilePath: str) -> list[Transaction]:

    dataFrame: pandas.DataFrame = pandas.read_csv(csvFilePath)
    transactions: list[Transaction] = []
    
    print(f'Parsing transactions from dataframe {csvFilePath}', flush=True, file=sys.stderr)

    for _, row in dataFrame.iterrows():
        t = Transaction.fromDataFrameRow(row)
        transactions.append(t)

    return transactions

def getLatestCachedCsvFile() -> str:
    return os.path.join(REPORTS_DIR, 'cached.csv')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Parse an account activity report from Bank Audi')
    parser.add_argument('--csv', action='store_true', default=False, help='Output in csv format')

    limitArg = parser.add_argument_group()
    limitArg.add_argument('--all', action='store_true', help='Show all transactions, overrides --limit', default=False)

    fileType = parser.add_mutually_exclusive_group()
    fileType.add_argument('--refresh', action='store_true', help='Parse and cache "./Reports/audi.pdf"')

    # String filters
    filterArg = parser.add_argument_group()
    filterArg.add_argument('-a', '--account', type=str, help='--account=X: only transactions for account X')
    filterArg.add_argument('-d', '--desc', type=str, help='--desc=X: only transactions with "X" in the description')
    filterArg.add_argument('-t', '--type', type=str, help='--type=X: only transactions of type X')
    filterArg.add_argument('-x', '--exclude', type=str, help='--exclude=X: exclude transactions with "X" in the description or category')

    # Date filters
    filterArg.add_argument('--after', type=str, help='--after=dd-mm-yyyy: only transactions after this date', default=None)
    filterArg.add_argument('--before', type=str, help='--before=dd-mm-yyyy: only transactions before this date', default=None)

    # Currency
    parser.add_argument('-c', '--currency', type=str, help='Example: --currency=EUR, convert all transactions to this currency', default='USD')

    args = parser.parse_args()

    transactions: list[Transaction] = []
    portfolio: Portfolio = None

    if args.refresh:

        audiPdf = os.path.join(REPORTS_DIR, 'audi.pdf')
        if not os.path.exists(audiPdf) or os.path.getsize(audiPdf) == 0:
            print(f'Looks like there is nothing to refresh from.\nMake sure {audiPdf} exists and is not empty.', file=sys.stderr)
            exit(1)

        bankAudi = Account('Bank Audi', 'USD', transactionsFromBankAudiPDF(audiPdf, cacheAfterParsingPath=os.path.join(REPORTS_DIR, 'audi_copy.pdf')))
        revolutUsd = Account('Revolut USD', 'USD', transactionsFromRevolutCSV(os.path.join(REPORTS_DIR, 'revolut_usd.csv')))
        revolutEur = Account('Revolut EUR', 'EUR', transactionsFromRevolutCSV(os.path.join(REPORTS_DIR, 'revolut_eur.csv')))

        cacheAccount(bankAudi)
        cacheAccount(revolutUsd)
        cacheAccount(revolutEur)

        today: str = datetime.now().strftime('%Y-%m-%d')
        GlobalEnv().updateEncryptedFiles(f'update finance transactions as of {today}', cmdFallback=True)

    else: # if not refreshing, read from cached csv
        
        bankAudi = Account('Bank Audi', 'USD', transactionsFromCachedCsv(os.path.join(CACHE_DIR, 'bank_audi.csv')))
        revolutUsd = Account('Revolut USD', 'USD', transactionsFromCachedCsv(os.path.join(CACHE_DIR, 'revolut_usd.csv')))
        revolutEur = Account('Revolut EUR', 'EUR', transactionsFromCachedCsv(os.path.join(CACHE_DIR, 'revolut_eur.csv')))

    portfolio = Portfolio('USD')
    portfolio.withAccount(bankAudi)
    portfolio.withAccount(revolutUsd)
    portfolio.withAccount(revolutEur)

    filter: TransactionFilter = TransactionFilter()
    filter.account = args.account
    filter.description = args.desc
    filter.type = TransactionType[str(args.type)] if args.type else None

    if args.after:
        filter.dateLowerBound = datetime.strptime(args.after, "%d-%m-%Y").date()
    if args.before:
        filter.dateUpperBound = datetime.strptime(args.before, "%d-%m-%Y").date()

    portfolio.withFilter(filter)

    if args.exclude:
        print(f'Exclude filter not implemented yet, ignoring --exclude={args.exclude}', flush=True, file=sys.stderr)

    portfolioAccount: Account = portfolio.build()

    assert Currency.currencySupported(args.currency), f'Currency not supported: {args.currency}'
    portfolioAccount.convertToCurrency(args.currency)

    if not args.csv:
        portfolioAccount.addTotal()
        [t.prepareForPrettyPrint() for t in portfolioAccount.transactions]

    pipedOutput = bool(not sys.stdout.isatty())
    filterApplied = bool(args.desc or args.type or args.after or args.before)

    fullOutput: bool = False
    fullOutput |= filterApplied
    fullOutput |= pipedOutput
    fullOutput |= args.all
    fullOutput |= args.csv

    if fullOutput:
        printObjectList(portfolioAccount.transactions, args.csv)
        exit(0)

    printObjectList(portfolioAccount.transactions[:20], csv=False)
    print(f'\n...<only showing 20>', file=sys.stderr)
    exit(0)