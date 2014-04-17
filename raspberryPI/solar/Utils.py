import re
import datetime
import os
import json


def getLastLine(filename, pattern, read_size=1024, max_lines=100):
    """return last lines of a file matching pattern.

    Only check up to *max_lines* lines.

    Returns an empty string if file is empty or no line
    matches the pattern.
    """

    # U is to open it with Universal newline support
    f = open(filename, 'rU')
    offset = read_size
    f.seek(0, 2)
    file_size = f.tell()
    if file_size == 0:
        return ""
    nlines = 0
    while 1:
        if file_size < offset:
            offset = file_size
        f.seek(-1 * offset, 2)
        read_str = f.read(offset)
        # Remove newline at the end
        if read_str[offset - 1] == '\n':
            read_str = read_str[:-1]
        lines = read_str.split('\n')
        nlines += len(lines)
        matching = [x for x in lines if pattern.search(x)]
        if len(matching) > 1:
            return matching[-1]
        if nlines > max_lines:
            return ""
        if offset == file_size:   # reached the beginning
            return read_str
        offset += read_size
    f.close()


def getStatusFromLog(logfile, max_delta=120):
    '''extract status information from *logfile*.

    Returns a list of tuples.
    '''

    lastline = getLastLine(logfile, re.compile("INFO - status"))

    d_date, d_time, status = re.match(
        "(\S+) (\S+) - DaemonLog - INFO - status: (\S+)",
        lastline).groups()

    current_time = datetime.datetime.now()
    log_time = datetime.datetime.strptime(
        "%s %s" % (d_date, d_time),
        "%Y-%m-%d %H:%M:%S,%f")

    delta = current_time - log_time
    if delta.total_seconds() > max_delta:
        return [(os.path.basename(logfile), 'na')]
    else:
        results = []
        for section in status.split(","):
            results.append(section.split("="))
        return results


def statusToHTML(status):
    '''convert status strings to html
    '''

    status_string = []
    for key, value in status:
        if value == "ok":
            status_string.append(
                '<img border="0" src="../images/pass.png">')
        elif value == "fail":
            status_string.append(
                '<img border="0" src="../images/fail.png">')
        elif value == "na":
            status_string.append(
                '<img border="0" src="../images/not_available.png">')

    status_string = " ".join(status_string)
    return status_string


def time2float(timeval):
    '''converts a x:xx value to hrs.'''
    hours, minutes = timeval.split(":")
    return float(hours) + float(minutes) / 60.0


def parseWeather(infile):
    '''parse weather information from download of
    wunderground URL
    '''

    station, temperature = None, None
    wind_direction, wind_speed = None, None

    keep = False
    take = []
    for x in infile:
        if x.startswith("{"):
            keep = True
        elif x.startswith(";"):
            break
        if keep:
            take.append(x)

    txt = "".join(take)
    
    decoded = json.loads(txt)
    current = decoded["current_observation"]
    return dict((
        ("temperature", current["temperature"]),
        ("wind_direction", current["wind_dir_degrees"]),
        ("wind_speed", current["wind_speed"])))

