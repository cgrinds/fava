#!/usr/bin/python3

import sys
from datetime import datetime, timedelta

from modgrammar import *

from beancount.core.amount import Amount, decimal

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)


class Budgets(object):

    def __init__(self, accounts):
        super(Budgets, self).__init__()
        self.accounts = accounts

    def budget(self, account_name, currency_name, date_from, date_to):
        # find account
        account = None
        for account_ in self.accounts:
            if account_.name == account_name:
                account = account_
                break

        if account == None:
            # print("budget fails account", account_name)
            return None

        # find right currency
        datelines = []
        for dateline in account.datelines:
            if dateline.currency == currency_name:
                datelines.append(dateline)

        if len(datelines) < 1:
            # print("budget fails currency", currency_name)
            return None

        # find lower boundry
        if datelines[0].date_monday > date_from:
            # print("budget fails lower", date_from)
            return None

        budget = 0
        for single_day in daterange(date_from, date_to):
            matching_dateline = self._matching_dateline(datelines, single_day)
            budget = budget + (matching_dateline.value / matching_dateline.days)

        return budget

    def _matching_dateline(self, datelines, date_):
        daily_value = 0
        last_seen_dateline = datelines[0].date_monday
        for dateline in datelines:
            if dateline.date_monday <= date_:
                last_seen_dateline = dateline
            else:
                break
        return last_seen_dateline


class Dateline(object):

    def __init__(self, date_monday, period, value, currency):
        super(Dateline, self).__init__()
        self.date_monday = date_monday
        self.period = period
        self.value = value
        self.currency = currency

        self.days = self._days(self.date_monday, self.period)

    def _days(self, start_date, period):
        # TODO test this extensively, may be buggy
        if period == 'D':
            return 1
        if period == 'W':
            return 7
        if period == 'M':
            return (start_date.replace(month = start_date.month % 12 +1, day = 1) - timedelta(days=1)).day
        if period == 'Q':
            month1 = days_in_period(datetime(start_date.year, start_date.month, 1), 'M')
            month2 = days_in_period(datetime(start_date.year, start_date.month+1, 1), 'M')
            month3 = days_in_period(datetime(start_date.year, start_date.month+2, 1), 'M')
            return ((start_date + timedelta(days=(month1+month2+month3))) - start_date).days
        if period == 'Y':
            return ((start_date + timedelta(years=1)) - start_date).days
        raise Exception("Period unknown: {}".format(period))


class AccountEntry(object):

    def __init__(self, name):
        super(AccountEntry, self).__init__()
        self.name = name
        self.datelines = []

#####

grammar_whitespace_mode = 'optional'

class DateExpr(Grammar):
    """
    A date can represented in these ways:
        2016-01-01 => Budget for a day
        2016-W01   => Budget for a week
        2016-01    => Budget for a month
        2016-Q1    => Budget for a quarter
        2016       => Budget for a year

    Returns a tuple of (date, 'D|W|M|Q|Y') where 'D|W|M|Q|Y' is the period
    """
    grammar = (WORD('0-9'), OR(GRAMMAR((WORD('-'), WORD('0-9'), WORD('-'), WORD('0-9'))) | GRAMMAR(WORD('-'), L('W'), WORD('0-9')) | GRAMMAR(WORD('-'), L('Q'), WORD('0-9'))))

    def value(self):
        if self.string.count('-') == 2:     # 2016-01-01
            return ('D', datetime.strptime(self.string, "%Y-%m-%d").date())
        elif 'W' in self.string:   # 2016-W01
            return ('W', datetime.strptime(self.string + '-1', "%Y-W%U-%w").date())
        elif 'Q' in self.string:   # 2016-Q1
            if 'Q1' in self.string:
                return ('Q', datetime.strptime(self.string + '-01-01', "%Y-Q1-%m-%d").date())
            elif 'Q2' in self.string:
                return ('Q', datetime.strptime(self.string + '-04-01', "%Y-Q2-%m-%d").date())
            elif 'Q3' in self.string:
                return ('Q', datetime.strptime(self.string + '-07-01', "%Y-Q3-%m-%d").date())
            elif 'Q4' in self.string:
                return ('Q', datetime.strptime(self.string + '-10-01', "%Y-Q4-%m-%d").date())
            else:
                raise Exception("Invalid date-string: {}".format(self.string))
        elif '-' in self.string:   # 2016-01
            return ('M', datetime.strptime(self.string + '-01', "%Y-%m-%d").date())
        else:                      # 2016
            return ('Y', datetime.strptime(self.string + '-01-01', "%Y-%m-%d").date())

class ValueExpr(Grammar):
    grammar = (OPTIONAL(WORD('-')), WORD('0-9'), WORD('.'), WORD('0-9'))

    def value(self):
        return decimal.Decimal(float(self.string))

class CurrencyExpr(Grammar):
    grammar = (WORD('A-Z'))

    def value(self):
        return self.string

class AccountNameExpr(Grammar):
    grammar = WORD("A-Za-z1-9:")

    def value(self):
        return AccountEntry(name=self.string)

class DatelineExpr(Grammar):
    grammar = (ONE_OR_MORE((DateExpr, ValueExpr, CurrencyExpr)))

    def value(self):
        value = []
        for e in self[0]:
            value.append(Dateline(date_monday=e[0].value()[1], period=e[0].value()[0], value=e[1].value(), currency=e[2].value()))
        return value

class EntryExpr(Grammar):
    grammar = (AccountNameExpr, ONE_OR_MORE(DatelineExpr))

    def value(self):
        entry = self[0].value()

        for e in self[1]:
            entry.datelines = sorted(e.value(), key=lambda dateline: dateline.date_monday)

        return entry

class AllExpr(Grammar):
    grammar = (ONE_OR_MORE(EntryExpr))

    def value(self):
        return [e.value() for e in self[0]]


# def run():
#     text = """
#     Expenses:Foo
#         2016-W01      70.00 USD
#         2016-W02     350.00 USD

#     Expenses:Foo2
#         2016-W31     250.00 USD
#         2016-W30     111.00 EUR
#         2016-W20    9999.15 USD
#     """

#     parser = AllExpr.parser()
#     result = parser.parse_text(text, eof=True)
#     remainder = parser.remainder()
#     print("Text: \n{}".format(text))
#     print("Parsed Text: {}".format(result))
#     print("Unparsed Text: {}".format(remainder))
#     print("\n\n\nValue: {}".format(result.value()))
#     print("\n\n\nResult: {}".format(len(result.elements[0])))
#     return Budgets(accounts=result.value())

# if __name__ == '__main__':
#     # text = sys.argv[1]
#     d = run()
#     print("##################")
#     date_from = datetime(2016, 1, 4)
#     date_to = datetime(2016, 1, 12)
#     print(d.budget('Expenses:Foo', 'USD', date_from, date_to))
