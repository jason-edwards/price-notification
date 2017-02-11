__author__ = 'jason'

from datagrabber import DataGrabber
from sqladaptor import DBConnector
from daemon import Daemon
import threading
import time
import sys
#import datetime
#import platform

DATAGRAB_SLEEP_TIME = 10 # seconds between each round of data grabbing
datagrab_thread= None

class DataGrabThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.keep_running = True

    def run(self):

        asx_codes_array = ["anz", "cba", "wbc", "cim"]
        #asx_codes_array = ["cba"]
        data_grabber = DataGrabber()
        print("Starting datagrab thread loop. This message should only appear once.")
        print(self.keep_running)
        while self.keep_running:
            seconds = 0
            for asx_code in asx_codes_array:
                print("Executing datagrab(" + asx_code + ") in main")
                data_grabber.data_grab(asx_code)
            print("Sleeping.")
            while seconds < DATAGRAB_SLEEP_TIME and self.keep_running:
                time.sleep(1)
                seconds += 1
        data_grabber.cleanup()


class MyDaemon(Daemon):
    def run(self):
        global datagrab_thread
        datagrab_thread = DataGrabThread()
        datagrab_thread.start()
        app.run(host='0.0.0.0', port=WEB_PORT)


if __name__ == "__main__":
    argc = len(sys.argv)

    if argc == 2:
        daemon = MyDaemon('/tmp/daemon-example.pid')
        if 'start' == sys.argv[1]:
            print("Starting as daemon.")
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            print("Restarting as daemon.")
            daemon.restart()
        elif 'history' == sys.argv[1]:
            print("usage: %s history code" % sys.argv[0])
            sys.exit(2)
        else:
            print("usage: %s start|stop|restart\n" % sys.argv[0])
            sys.exit(2)
    elif argc == 3:
        if 'history' == sys.argv[1]:
            data_grabber = DataGrabber()
            result = data_grabber.historic_data_grab(sys.argv[2])
        elif 'history_alt' == sys.argv[1]:
            data_grabber = DataGrabber()
            result = data_grabber.historic_data_grab_alt(sys.argv[2])
        else:
            print("Problems aye...")

        if result == 0:
            print("Database populated with historic data for %s" % sys.argv[2])
        elif result == 404:
            print("Could not find file for \'%s\'." % sys.argv[2])
            print("Check if code is valid.")
    else:
        print("Not running as daemon!")
        datagrab_thread = DataGrabThread()
        datagrab_thread.start()


    if datagrab_thread is not None:
        print("Waiting for datagrab thread")
        #datagrab_thread.keep_running = False
        datagrab_thread.join()

print("Exiting")