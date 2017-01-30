from trial import DBConnector, DataGrabber
from flask import Flask, render_template, request, redirect
from daemon import Daemon
import datetime
import threading
import platform
import time
import sys

WEB_PORT = 5000 if platform.system() == "Darwin" else 80
DATAGRAB_SLEEP_TIME = 10 # seconds between each round of data grabbing

app = Flask(__name__)
#app.debug = True
datagrab_thread = None


@app.route("/table")
@app.route("/table/<code>")
def table(code=None):
    if code is None:
        return "usage: ip_address/table/asx code"

    data = DBConnector()
    code, price, timestamp = data.get_current_record(code)
    return render_template('price.html', code=code, price=price, timestamp=timestamp)


@app.route("/graph/")
@app.route("/graph/<code>/")
@app.route("/graph/<code>/<time_frame>/")
def graph(code=None, time_frame=None):
    if code is None:
        return "usage: ip_address/graph/asx code"

    data = DBConnector()
    start_date = None
    end_date = None

    redirect_flag = False

    # Should be in format "Start-End" where dates are in format "YYYYMMDD"
    if time_frame is not None:
        dates_array = time_frame.split('-')
        if len(dates_array) == 2:
            try:
                start_date = datetime.datetime.strptime(dates_array[0], "%Y%m%d")
                end_date = datetime.datetime.strptime(dates_array[1], "%Y%m%d")
            except IndexError:
                redirect_flag = True
            except ValueError:
                redirect_flag = True
        else:
            redirect_flag = True

    if redirect_flag:
        redirect_url = "/graph/" + code + "/"
        return redirect(redirect_url)

    if (start_date is not None) & (end_date is not None):
        query = data.get_records_by_timeframe(code, start_date, end_date)
    else:
        query = data.get_records_by_timeframe(code)

    prices = []
    timestamps = []
    for rows in query:
        prices.append(float(rows.price))
        timestamps.append(str(rows.timestamp))
    prices.insert(0, "price")
    timestamps.insert(0, "timestamps")

    return render_template('graph.html', prices=str(prices), timestamps=str(timestamps))


class DataGrabThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.keep_running = True


    def run(self):
        asx_codes_array = ["anz", "cba", "wbc", "cim"]
        #asx_codes_array = ["cba"]
        data_grabber = DataGrabber()
        print "Starting datagrab thread loop. This message should only appear once."
        while self.keep_running:
            seconds = 0
            for asx_code in asx_codes_array:
                print "Executing datagrab(" + asx_code + ")"
                data_grabber.data_grab(asx_code)
            print "Sleeping."
            while seconds < DATAGRAB_SLEEP_TIME and self.keep_running:
                time.sleep(1)
                seconds += 1
        data_grabber.cleanup()


class MyDaemon(Daemon):
    def run(self):
        datagrab_thread = DataGrabThread()
        datagrab_thread.start()
        app.run(host='0.0.0.0', port=WEB_PORT)


if __name__ == "__main__":
    argc = len(sys.argv)

    if argc == 2:
        daemon = MyDaemon('/tmp/daemon-example.pid')
        if 'start' == sys.argv[1]:
            print "Starting as daemon."
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            print "Restarting as daemon."
            daemon.restart()
        elif 'history' == sys.argv[1]:
            print "usage: %s history code" % sys.argv[0]
            sys.exit(2)
        else:
            print "usage: %s start|stop|restart\n" % sys.argv[0]
            sys.exit(2)
    elif argc == 3:
        if 'history' == sys.argv[1]:
            data_grabber = DataGrabber()
            result = data_grabber.historic_data_grab(sys.argv[2])
        elif 'history_alt' == sys.argv[1]:
            data_grabber = DataGrabber()
            result = data_grabber.historic_data_grab_alt(sys.argv[2])
        else:
            print "Problems aye..."

        if result == 0:
            print "Database populated with historic data for %s" % sys.argv[2]
        elif result == 404:
            print "Could not find file for \'%s\'." % sys.argv[2]
            print "Check if code is valid."
    else:
        print "Not running as daemon!"
        datagrab_thread = DataGrabThread()
        datagrab_thread.start()
        app.run(host='0.0.0.0', port=WEB_PORT)

    if datagrab_thread is not None:
        print "Waiting for datagrab thread"
        datagrab_thread.keep_running = False
        datagrab_thread.join()

print "Exiting"