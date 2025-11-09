
import datetime
def parseDate(value: str | datetime.date, dateFormat: str = '%m/%d/%Y') -> datetime.date:

    assert value != None, 'date to parse is NONE'

    if isinstance(value, datetime.date):
        return value

    assert isinstance(value, str), f'can only parse date from str. got: {value}'

    return datetime.datetime.strptime(value, dateFormat).date()

def percentageDifference(v1: float, v2: float) -> float:

    if v1 == 0 and v2 == 0:
        return 0.0
    if v1 == 0:
        return float('inf')
    if v2 == 0:
        return float('inf')

    difference = abs(v1 - v2)
    average = (abs(v1) + abs(v2)) / 2
    
    return (difference / average) * 100

def withinPercentage(v1: float, v2: float, p: int) -> bool:

    if v1 == 0 and v2 == 0:
        return True

    if v1 == 0 or v2 == 0:
        return False

    return percentageDifference(v1, v2) <= p

def parseFloat(value: str | float) -> float:

    assert value != None, 'float value to parse is NONE'

    if isinstance(value, float) or isinstance(value, int):
        return value

    if not isinstance(value, str):
        raise ValueError(f'can only parse float from str, got {type(value)}')

    value = value.replace(',', '')
    return float(value)

def tryParseFloat(s: str) -> str | float:

    s = str(s)

    try:
        s = float(s)
    except ValueError:
        pass
    finally:
        return s