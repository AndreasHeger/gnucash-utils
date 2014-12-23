
import socket
import time


class Monitor:

    CARBON_SERVER = '192.168.0.51'
    CARBON_PORT = 2003

    label = None

    def __init__(self, logger, heart_beat=10):

        if self.label is None:
            raise NotImplementedError("derived class must set label")

        self.stdin_path = '/dev/null'
        # tty not available for a spice
        self.stdout_path = '/dev/null'
        self.stderr_path = '/dev/null'
        self.pidfile_path = '/mnt/ramdisk/%s_daemon.pid' % self.label
        self.pidfile_timeout = 5
        self.logger = logger
        self.heart_beat = heart_beat

        # open tcp connection
        self.connection = None

    def run(self):

        self.logger.debug("entered Monitor.run()")
        self.setup()

        self.logger.info(
            "starting main loop with heartbeat=%i" % self.heart_beat)

        while True:
            values = self.monitor()

            self.logger.debug("acquired values: %s" % str(values))
            self.updateDatabase(values)

            time.sleep(self.heart_beat)

    def setup(self):
        self.logger.info("monitoring initialization")

    def updateDatabase(self, values):
        '''send data to carbon server'''
        sock = socket.socket()
        try:
            sock.connect((self.CARBON_SERVER,
                          self.CARBON_PORT))
        except:
            self.logger.warn(
                "Couldn't connect to %(server)s on port %(port)d, "
                "is carbon running?" %
                {'server': self.CARBON_SERVER,
                 'port': self.CARBON_PORT})
            return

        now = int(time.time())
        lines = ["%s %s %d" % (sensor, value, now) for 
                 sensor, value in values.items()]

        # all lines must end in a newline
        message = '\n'.join(lines) + '\n'
        # print "sending message\n"
        # print '-' * 80
        # print message
        # print
        sock.sendall(message)
