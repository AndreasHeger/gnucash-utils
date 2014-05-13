import sqlite3
import sys
import os
import re
import optparse
import logging
import ConfigParser
import itertools
import collections

from csv import writer
from itertools import chain, izip
from lxml.etree import parse


def get_ts(c):
    """Return the unix timestamp component of an RRD XML date comment.

    >>> get_ts("<!-- 2011-04-28 19:18:40 BST / 1304014720 -->")
    '1304014720'

    """
    date, tstamp = c.split("/")
    return tstamp.strip()


def headers(tree):
    return (s.strip() for s in tree.xpath("//ds/name/text()"))


def iter_rra(tree):
    '''iterate over tree, yielding tuples of 
    (rra database, [timestamp, value1, value2, ...]).
    '''

    for rra_index, rra in enumerate(tree.xpath("//rra")):
        for data in rra.iter('database'):
            for row in data:
                if row.text:
                    ts = get_ts(row.text)
                else:
                    values = [x.text for x in row.findall("v")]
                    yield rra_index, [ts] + values


def createTables(dbh, databases, logger):
    '''create tables for databases.

    '''
    for key, data in databases.items():
        cc = dbh.cursor()

        prefix = data['prefix']

        for rra in data['rra']:
            tablename = prefix + key[:-4] + "_" + rra
            logger.info("creating table %s" % tablename)

            ff = ",".join(["%s FLOAT" % f for f in data['ds']])

            statement = '''
            CREATE TABLE %(tablename)s
            (time INT UNIQUE ON CONFLICT IGNORE, %(ff)s)
            ''' % locals()
            logger.debug(statement)
            try:
                cc.execute(statement)
            except sqlite3.OperationalError, msg:
                logger.warn("Could not create table %s: %s" % (tablename, msg))


def getNumRows(dbh, tablename):
    '''return number of rows in table'''
    statement = "SELECT COUNT(*) FROM %s" % (tablename)
    cc = dbh.cursor()
    cc.execute(statement)
    return cc.fetchone()[0]


def mirrorData(dbh, databases, user, host, logger, srcdir):
    '''mirror data from remote RRD database
    in local archive.
    '''

    for key, data in databases.items():
        cc = dbh.cursor()
        xml_file = key + ".xml"

        logger.debug("retrieving data for %s" % key)
        statement = 'ssh %(user)s@%(host)s "rrdtool dump %(srcdir)s/%(key)s" > %(xml_file)s' % locals()
        logger.debug(statement)
        os.system(statement)

        # parse data
        tree = parse(xml_file)

        ds = list(headers(tree))
        assert list(ds) == list(data['ds']), \
            "incompatible data source names: %s vs %s" % (list(ds),
                                                          list(data['ds']))

        # group by rra
        rras = itertools.groupby(iter_rra(tree),
                                 key=lambda x: x[0])

        prefix = data['prefix']

        for rra_index, values in rras:
            rra = data['rra'][rra_index]

            tablename = prefix + key[:-4] + "_" + rra
            logger.debug("working on table %s" % tablename)
            rows_before = getNumRows(dbh, tablename)

            values = [x[1] for x in values]
            logger.debug("parsing data - input: %i rows" % len(values))

            width = len(values[0]) - 1
            assert width == len(ds), \
                "incompatible number of data sources: %i vs %i" %\
                (width, len(ds))

            # remove NaN values and indices
            all_values = [x for x in values if x[1] != "NaN"]
            if len(all_values) == 0:
                logger.info("no data - skipped")
                continue

            logger.debug("retrieved %i data points: width=%i" %
                         (len(all_values), len(all_values[0])))

            columns = ",".join(ds)
            marks = ",".join("?" * (len(ds) + 1))
            statement = "INSERT INTO %(tablename)s (time,%(columns)s) VALUES (%(marks)s);" % locals(
            )
            logger.debug(statement)

            logger.debug("inserting data into %s" % tablename)
            cc.executemany(statement,
                           all_values)
            dbh.commit()

            rows_after = getNumRows(dbh, tablename)

            logger.info("updated table %s: before=%i, after=%i" %
                        (tablename, rows_before, rows_after))


def main(argv=None):

    if argv == None:
        argv = sys.argv

    parser = optparse.OptionParser()

    parser.add_option('--config', dest="config", type="string",
                      help="configuration file to use")

    parser.set_defaults(
        config='solar_mirror.ini')

    (options, args) = parser.parse_args(argv)

    if len(args) < 2:
        raise ValueError("please supply at least one command")

    commands = args[1:]

    # parse configuration file
    config = ConfigParser.RawConfigParser()
    config.read(options.config)

    databases = {}
    for section in config.sections():
        if not section.endswith(".rrd"):
            continue
        if config.has_option(section, 'rra'):
            rra = config.get(section, 'rra')
        else:
            rra = config.get('default', 'rra')

        if config.has_option(section, 'ds'):
            ds = config.get(section, 'ds')
        else:
            ds = config.get('default', 'ds')

        if config.has_option(section, 'prefix'):
            prefix = config.get(section, 'prefix')
        elif config.has_option('default', 'prefix'):
            prefix = config.get('default', 'prefix')
        else:
            prefix = ''

        values = {'rra': [x.strip() for x in rra.split(",")],
                  'ds': [x.strip() for x in ds.split(",")],
                  'prefix': prefix,
                  }
        databases[section] = values

    logger = logging.getLogger("SolarMirrorLog")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(config.get('default', 'log'))
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    dbh = sqlite3.connect(config.get('default', "database"))

    for command in commands:
        if command == "create":
            createTables(dbh,
                         databases,
                         logger=logger)

        elif command == "mirror":
            mirrorData(dbh,
                       databases,
                       user=config.get('default', 'user'),
                       host=config.get('default', 'host'),
                       srcdir=config.get('default', 'srcdir'),
                       logger=logger)
    logger.info("completed successfully")

if __name__ == "__main__":
    sys.exit(main(sys.argv))
