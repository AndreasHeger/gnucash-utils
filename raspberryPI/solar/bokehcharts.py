import sqlite3
import sys
import os
import optparse
import logging
import ConfigParser
import itertools
import bokeh.plotting


def outputCharts(dbh, config):
    '''output all data into highcharts'''

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
                xvals, yvals = zip(*cc)

                datasets.append((name, xvals, yvals))

        bokeh.plotting.output_file(section)
        fig = bokeh.plotting.figure()
        bokeh.plotting.hold(True)

        colors = bokeh.plotting.brewer["Spectral"][11]
        
        for x, vals in enumerate(datasets):
            name, xvalues, yvalues = vals
            l = bokeh.plotting.line(xvalues,
                                    yvalues,
                                    color=colors[x % len(colors)],
                                    line_width=2,
                                    x_axis_type='datetime',
                                    title=name,
                                    legend=name)
        bokeh.plotting.save()

        outfile = open("master_%s" % section, "w")

        outfile.write("""
<!DOCTYPE HTML>
<html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
    <title>Highcharts Example</title>
    </head>
    <body>
\n
""")

        outfile.write(l.create_html_snippet(
            server=False,
            embed_base_url="",
            embed_save_loc=".",
            static_path="/home/andreas/devel/Projects/raspberryPI/solar/"))
        outfile.write("""
Body
</body>
</html>
""")
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

    outputCharts(dbh, config)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
