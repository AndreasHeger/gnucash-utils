import sqlite3
import sys
import os
import optparse
import logging
import ConfigParser
import itertools
import jinja2


def outputHighcharts(dbh, config):
    '''output all data into highcharts'''

    # load templates from current directory
    templateLoader = jinja2.FileSystemLoader(searchpath=".")

    # An environment provides the data necessary to read and
    #   parse our templates.  We pass in the loader object here.
    templateEnv = jinja2.Environment(loader=templateLoader)

    # This constant string specifies the template file we will use.
    TEMPLATE_FILE = "highchart.jinja"

    # Read the template file using the environment object.
    # This also constructs our Template object.
    template = templateEnv.get_template(TEMPLATE_FILE)

    cc = dbh.cursor()

    for section in config.sections():
        if not section.endswith(".html"):
            continue
        datasets = []
        for option in config.options(section):
            if option.startswith("track"):
                values = config.get(section, option)
                parts = values.split(",")
                if len(parts) == 4:
                    name, table, column1, column2 = parts
                elif len(parts) == 1:
                    name = column2 = parts[0]
                elif len(parts) == 2:
                    name, table = parts
                    column2 = name
                elif len(parts) == 3:
                    name, table, column1 = parts
                    column2 = name
                
                ##########################################################
                # 1000 to convert from unix time-stamp to javascript time
                try:
                    cc.execute("SELECT %s, %s FROM %s" %
                               (column1, column2, table))
                except sqlite3.OperationalError, msg:
                    print column1, column2, table
                    raise
                data = ",".join(["[%i,%f]" % (x, y) for x, y
                                 in cc])
                datasets.append((name, data))

        data = ",".join(["""{
        name : '%s',
        data : [%s]
        }""" % (x, y) for x, y in datasets])

        templateVars = {
            'data': data,
            'title': config.get(section, 'title'),
            'xlabel': config.get(section, 'xlabel'),
            'ylabel': config.get(section, 'ylabel'),
        }

        # Finally, process the template to produce our final text.
        outfile = open(section, "w")
        outfile.write(template.render(templateVars))
        outfile.close()

    

                  

def main(argv=None):

    if argv is None:
        argv = sys.argv

    parser = optparse.OptionParser()

    parser.add_option('--config', dest="config", type="string",
                      help="configuration file to use")

    parser.set_defaults(
        config='highcharts.ini')

    (options, args) = parser.parse_args(argv)

    if len(args) < 2:
        raise ValueError("please supply at least one command")

    commands = args[1:]

    # parse configuration file
    config = ConfigParser.RawConfigParser()
    config.read(options.config)

    # logger = logging.getLogger("SolarMirrorLog")
    # logger.setLevel(logging.DEBUG)
    # formatter = logging.Formatter(
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # handler = logging.FileHandler(config.get('default', 'log'))
    # handler.setFormatter(formatter)
    # logger.addHandler(handler)

    dbh = sqlite3.connect(config.get('default', "database"))

    outputHighcharts(dbh, config)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
