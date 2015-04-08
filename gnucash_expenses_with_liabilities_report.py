#!/usr/bin/env python
'''
gnucash_expenses_with_liability_report.py - Expense report incl. liabilities
============================================================================

:author: Andreas Heger

This report collects expenses and selected liabilities in order to
arrive at a monthly total of payments.

In home budgeting, this script is useful to get an overview over
where monthly out-goings end up. This seems to be common problem:

http://lists.gnucash.org/pipermail/gnucash-user/2006-June/016662.html

http://money.stackexchange.com/questions/20914/show-liability-payments-with-expenses

Usage
-----

Invoke this script like the following example::

   python gnucash_expenses_with_liability_report.py \
       --gnucash-file=home_budget

This will do the analysis on :file:`home_budget.xac`.
The output goes to stdout and is in tab separated values format.
The report can be easily plotted in a spreadsheet application
or any other statistics package.

Type::

   python gnucash_expenses_with_liability_report.py --help

for command line options.

'''

# Derived from an example within gnucash distribution.
#
# Copyright (C) 2009, 2010 ParIT Worker Co-operative <transparency@parit.ca>
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact:
# Free Software Foundation           Voice:  +1-617-542-5942
# 51 Franklin Street, Fifth Floor    Fax:    +1-617-542-2652
# Boston, MA  02110-1301,  USA       gnu@gnu.org
#
# @author Mark Jenkins, ParIT Worker Co-operative <mark@parit.ca>

# python imports
from sys import argv, stdout
from datetime import date, timedelta
from bisect import bisect_right
from decimal import Decimal
from math import log10
import csv

# gnucash imports
import gnucash
from gnucash import Session, GncNumeric, Split
from gnucash.gnucash_core_c import \
    GNC_DENOM_AUTO, GNC_HOW_DENOM_EXACT, \
    ACCT_TYPE_ASSET, ACCT_TYPE_BANK, ACCT_TYPE_CASH, ACCT_TYPE_CHECKING, \
    ACCT_TYPE_CREDIT, ACCT_TYPE_EQUITY, ACCT_TYPE_EXPENSE, ACCT_TYPE_INCOME, \
    ACCT_TYPE_LIABILITY, ACCT_TYPE_MUTUAL, ACCT_TYPE_PAYABLE, \
    ACCT_TYPE_RECEIVABLE, ACCT_TYPE_STOCK, ACCT_TYPE_ROOT, ACCT_TYPE_TRADING

import Experiment as E

# a dictionary with a period name as key, and number of months in that
# kind of period as the value
PERIODS = {"monthly": 1,
           "quarterly": 3,
           "yearly": 12}

NUM_MONTHS = 12
ONE_DAY = timedelta(days=1)
ZERO = Decimal(0)

DEBITS_SHOW, CREDITS_SHOW = ("debits-show", "credits-show")


def gnc_numeric_to_python_Decimal(numeric):
    negative = numeric.negative_p()
    if negative:
        sign = 1
    else:
        sign = 0
    copy = GncNumeric(numeric.num(), numeric.denom())
    result = copy.to_decimal(None)
    if not result:
        raise Exception("gnc numeric value %s can't be converted to deciaml" %
                        copy.to_string())
    digit_tuple = tuple(int(char)
                        for char in str(copy.num())
                        if char != '-')
    denominator = copy.denom()
    exponent = int(log10(denominator))
    assert((10 ** exponent) == denominator)
    return Decimal((sign, digit_tuple, -exponent))


def next_period_start(start_year, start_month, period_type):
    # add numbers of months for the period length
    end_month = start_month + PERIODS[period_type]
    # use integer division to find out if the new end month is in a different
    # year, what year it is, and what the end month number should be changed
    # to.
    # Because this depends on modular arithmatic, we have to curvert the month
    # values from 1-12 to 0-11 by subtracting 1 and putting it back after
    #
    # the really cool part is that this whole thing is implemented without
    # any branching; if end_month > NUM_MONTHS
    #
    # A the super nice thing is that you can add all kinds of period lengths
    # to PERIODS
    end_year = start_year + ((end_month - 1) / NUM_MONTHS)
    end_month = ((end_month - 1) % NUM_MONTHS) + 1

    return end_year, end_month


def period_end(start_year, start_month, period_type):
    if period_type not in PERIODS:
        raise Exception("%s is not a valid period, should be %s" % (
            period_type, str(PERIODS.keys())))

    end_year, end_month = next_period_start(start_year, start_month,
                                            period_type)

    # last step, the end date is day back from the start of the next period
    # so we get a period end like
    # 2010-03-31 for period starting 2010-01 instead of 2010-04-01
    return date(end_year, end_month, 1) - ONE_DAY


def generate_period_boundaries(start_year, start_month, period_type, periods):
    for i in xrange(periods):
        yield (date(start_year, start_month, 1),
               period_end(start_year, start_month, period_type))
        start_year, start_month = next_period_start(start_year, start_month,
                                                    period_type)


def account_from_path(top_account, account_path, original_path=None):
    '''account path is list of account names (branch in account tree).'''
    if original_path == None:
        original_path = account_path
    account, account_path = account_path[0], account_path[1:]
    account = top_account.lookup_by_name(account)
    if account.get_instance() == None:
        raise Exception(
            "path " + ''.join(original_path) + " could not be found")
    if len(account_path) > 0:
        return account_from_path(account, account_path, original_path)
    else:
        return account


def filterAccounts(results,
                   root_account,
                   criteria,
                   ignore=None,
                   level=0):
    '''walk over account hierarchy starting at *root_account* and 
    return accounts matching a list of *criteria* in *results*.

    *ignore* is an optional set of acount names to ignore.
    '''
    for child in root_account.get_children():
        # child = gnucash.Account(instance=child)
        if ignore and child.GetName() in ignore:
            continue
        for criterion in criteria:
            if criterion(child, level):
                results.append(child)
                break
        else:
            filterAccounts(results, child, criteria, ignore, level + 1)

    return results


def accumulateAccount(account_of_interest,
                      period_list,
                      max_transaction=0):
    '''accumulate transactions for account.

    Ignore transaction above max_transaction size
    '''

    # a copy of the above list with just the period start dates
    period_starts = [e[0] for e in period_list]

    # insert and add all splits in the periods of interest
    for split in account_of_interest.GetSplitList():
        trans = split.parent
        trans_date = date.fromtimestamp(trans.GetDate())

        # use binary search to find the period that starts before or on
        # the transaction date
        period_index = bisect_right(period_starts, trans_date) - 1

        # ignore transactions with a date before the matching period start
        # (after subtracting 1 above start_index would be -1)
        # and after the last period_end
        if period_index >= 0 and \
                trans_date <= period_list[len(period_list) - 1][1]:

            # get the period bucket appropriate for the split in question
            period = period_list[period_index]

            # more specifically, we'd expect the transaction date
            # to be on or after the period start, and  before or on the
            # period end, assuming the binary search (bisect_right)
            # assumptions from above are are right..
            #
            # in other words, we assert our use of binary search
            # and the filtered results from the above if provide all the
            # protection we need
            assert(trans_date >= period[0] and trans_date <= period[1])

            split_amount = gnc_numeric_to_python_Decimal(split.GetAmount())

            # if the amount is negative, this is a credit
            if split_amount < ZERO:
                debit_credit_offset = 1
            # else a debit
            else:
                debit_credit_offset = 0

            if max_transaction and abs(split_amount) > max_transaction:
                continue

            # store the debit or credit Split with its transaction, using the
            # above offset to get in the right bucket
            #
            # if we wanted to be really cool we'd keep the transactions
            period[2 + debit_credit_offset].append((trans, split))

            # add the debit or credit to the sum, using the above offset
            # to get in the right bucket
            period[4 + debit_credit_offset] += split_amount


def accumulateAccountWithChildren(account_of_interest,
                                  period_list,
                                  max_transaction=0):
    '''accumulate credits and debits from account
    including child accounts.'''
    accumulateAccount(account_of_interest, period_list, max_transaction)
    for child in account_of_interest.get_children():
        accumulateAccountWithChildren(child, period_list, max_transaction)


def buildPeriodList(start_year, start_month, period_type, periods):
    '''return a list of all the periods of interest, for each period
    keep the start date, end date, a list to store debits and credits,
    and sums for tracking the sum of all debits and sum of all credits
    '''
    period_list = [
        [start_date, end_date,
         [],  # debits
         [],  # credits
         ZERO,  # debits sum
         ZERO,  # credits sum
         ]
        for start_date, end_date in generate_period_boundaries(
            start_year, start_month, period_type, periods)
    ]

    return period_list


def outputAccount(period_list, debits_show, credits_show):
    '''ouput data to stdout.

    For debugging purposes.
    '''
    csv_writer = csv.writer(stdout)
    csv_writer.writerow(('period start', 'period end', 'debits', 'credits'))

    def generate_detail_rows(values):
        return (
            ('', '', '', '', trans.GetDescription(),
             gnc_numeric_to_python_Decimal(split.GetAmount()))
            for trans, split in values)

    for start_date, end_date, debits, credits, debit_sum, credit_sum in \
            period_list:
        csv_writer.writerow((start_date, end_date, debit_sum, credit_sum))

        if debits_show and len(debits) > 0:
            csv_writer.writerow(
                ('DEBITS', '', '', '', 'description', 'value'))
            csv_writer.writerows(generate_detail_rows(debits))
            csv_writer.writerow(())
        if credits_show and len(credits) > 0:
            csv_writer.writerow(
                ('CREDITS', '', '', '', 'description', 'value'))
            csv_writer.writerows(generate_detail_rows(credits))
            csv_writer.writerow(())


def sumCounts(data):
    '''aggregate list of counts.'''
    sum_values = [sum(x) for x in zip(*data[1:])]
    return sum_values


def main():

    parser = E.OptionParser()

    parser.add_option(
        "-g", "--gnucash-file", dest="gnucash_file", type="string",
        help="gnucash file to use [%default]")

    parser.add_option(
        "-y", "--year", dest="start_year", type="int",
        help="year to start counting [%default]")

    parser.add_option(
        "-n", "--number-of-periods", dest="periods", type="int",
        help="number of periods [%default]")

    parser.add_option(
        "-a", "--number-of-accounts", dest="num_accounts", type="int",
        help="number of accounts to show [%default]")

    parser.add_option(
        "-m", "--month", dest="start_month", type="int",
        help="month to start counting [%default]")

    parser.add_option(
        "-x", "--max-transaction", dest="max_transaction", type="float",
        help="maximum value of a transaction "
        " Use this to filter out large atypical expenses"
        " [%default]")

    parser.add_option(
        "-p", "--period-type", dest="period_type", type="choice",
        choices=("monthly", "quarterly", "yearly", ),
        help="period type [%default]")

    parser.set_defaults(
        num_accounts=10,
        start_year=2009,
        start_month=1,
        period_type="monthly",
        periods=36,
        gnucash_file="andreas-coop",
        accounts_to_ignore=["House Purchase"],
        max_transaction=100000,
    )

    options, args = E.Start(parser)

    # open - ignore lock as we only read
    gnucash_session = Session(options.gnucash_file,
                              is_new=False,
                              ignore_lock=True)

    root_account = gnucash_session.book.get_root_account()

    accounts = []

    # criteria for account selection - combined with OR
    criteria = [
        lambda a, l: a.GetType() == ACCT_TYPE_EXPENSE and l >= 1,
        lambda a, l: a.GetName() == "Mortage",
    ]

    filterAccounts(accounts, root_account,
                   criteria,
                   ignore=options.accounts_to_ignore,
                   )

    data = []

    for account in accounts:
        E.debug("processing %s" % account.GetName())
        period_list = buildPeriodList(options.start_year,
                                      options.start_month,
                                      options.period_type,
                                      options.periods)

        accumulateAccountWithChildren(account, period_list,
                                      options.max_transaction)

        # collect balances - debits are positive
        balances = []
        for start_date, end_date, debits, credits, debit_sum, credit_sum in \
                period_list:
            balances.append(credit_sum + debit_sum)

        data.append((sum(balances), account, balances))

    # sort data by total ammount
    data.sort()

    # output data
    data.reverse()

    # print "\n".join( map(str, [ (x[1].GetName(), x[0]) for x in data ]))

    # collect column headers
    headers = [x[1].GetName() for x in data[:options.num_accounts]] + ["other"]

    options.stdout.write("start\t%s\n" % "\t".join(headers))

    # aggregate columns, returns a modified data matrix
    detail = zip(*[x[2] for x in data[:options.num_accounts]])
    other = sumCounts([x[2] for x in data[options.num_accounts:]])
    period_list = buildPeriodList(options.start_year,
                                  options.start_month,
                                  options.period_type,
                                  options.periods)

    for p, d, o in zip(period_list, detail, other):
        options.stdout.write("\t".join(map(str,
                                           (p[0],
                                            "\t".join(map(str, d)),
                                            str(o)))) + "\n")

    E.Stop()

    # no save needed, we're just reading..
    # when calling end and no lock, error message appears:
    # * 20:47:09  WARN <gnc.backend> [xml_session_end()] Error on g_unlink(andreas-coop.LCK): 2: No such file or directory
    # Afraid that this might cause an existing session to
    # crash, so the following is disabled:
    #
    # gnucash_session.end()


if __name__ == "__main__":
    main()
