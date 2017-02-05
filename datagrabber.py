__author__ = 'jason'

from selenium import webdriver
import requests as req
from daemon import Daemon
from datasourceyahoofinance import DatasourceYahoofinance
from datasourceasx import DataSourceASX
import platform
import datetime
import sys
import re
import csv
from time import time, sleep
from bs4 import BeautifulSoup
from sqladaptor import PriceLog, DBConnector
import logging

DATAGRAB_SLEEP_TIME = 10 # seconds between each round of data grabbing

logger = logging.basicConfig(filename='datagrabber.log',level=logging.DEBUG)


class DataGrabber():

    def __init__(self):
        self.browser = webdriver.PhantomJS('./phantomjs') if platform.system() != "Darwin" else webdriver.PhantomJS()
        self.keep_running = True

    def cleanup(self):
        self.browser.close()

    def run(self):
        asx_codes_array = ["anz", "cba", "wbc", "cim"]
        print("Starting datagrab thread loop. This message should only appear once.")
        logging.debug("DataGrabber.run(): Starting loop")
        while self.keep_running:
            seconds = 0
            for asx_code in asx_codes_array:
                print("Executing datagrab(%s)" % asx_code)
                data_grabber.price_grab(asx_code)
            print("Sleeping.")
            while seconds < DATAGRAB_SLEEP_TIME and self.keep_running:
                sleep(1)
                seconds += 1
        logging.debug("daemon.cleanup()")
        data_grabber.cleanup()

    def data_grab(self, code):
        start_time = time()

        url_container_list = [DataSourceASX(asx_code=code), DatasourceYahoofinance(asx_code=code)]

        for url_container in url_container_list:
            try:
                current_price = url_container.get_price()
                break
            except LookupError:
                continue

        request_time = time() - start_time
        print("\tTook %.2f seconds to get response." % request_time)

        print("\t%s\t%s" % (code, current_price))

        price_log = PriceLog(
            asx_code=code,
            price=current_price,
            timestamp=datetime.datetime.now()
        )

        try:
            price_log.save()
        except:
            print("\tError saving to database.")

        finish_time = time() - start_time
        print("\tSaved in database. Total time: %.2f" % finish_time)
        return 0

    def historic_data_grab(self, code):
        url_string = "https://au.finance.yahoo.com/q/hp?s=" + code + ".AX"

        page = req.get(url_string)
        html_source = page.text

        soup = BeautifulSoup(html_source)
        search_id_string = 'rightcol'
        try:
            file_url = (soup.find(id=search_id_string)
                        .find_all('a', href=re.compile('^http://real-chart.finance'))[0].get('href'))
        except AttributeError:
            print("Attribute Error: bs4.find() could no1t retrieve text for %s." % code)
            print("Check the status of the webpage.")
            return 404

        #csv_file = urllib2.urlopen(file_url)
        csv_file = req.get(file_url)
        reader = csv.reader(csv_file)

        print("%s history read." % code)
        data_array = []

        # Construct data_array to contain dictionary of price_log data.
        reader.next()
        for row in reader:
            # Columns are - Date, Open, High, Low, Close, Volume, Adjusted Close

            # Add in database for the price at open. The time is 10:00:00 AEST -> 00:00:00 UTC
            date_string = row[0] + " 00:00:00"
            timestamp = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

            data = {'asx_code': code, 'price': row[1], 'timestamp': timestamp}
            data_array.append(data)

            # Add in database for the price at close. The time is 16:00:00 AEST -> 06:00:00 UTC
            date_string = row[0] + " 06:00:00"
            timestamp = datetime.datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")

            data = {'asx_code': code, 'price': row[4], 'timestamp': timestamp}
            data_array.append(data)

        db_instance = DBConnector()
        insert_array = []
        skipped_array = []
        for element in data_array:
            query = db_instance.get_pricelog_record(code=element['asx_code'],
                                                    start_time=element['timestamp']-datetime.timedelta(minutes=30),
                                                    end_time=element['timestamp']+datetime.timedelta(minutes=30))
            if query.count() == 0:
                insert_array.append(element)
            else:
                skipped_array.append(element)

        if len(insert_array) != 0:
            PriceLog.insert_many(insert_array).execute()

        print(len(insert_array), "items inserted")
        print(len(skipped_array), "items skipped for", code)
        return 0


class MyDaemon(Daemon):
    def run(self):
        data_grabber.run()


if __name__ == "__main__":
    data_grabber = DataGrabber()
    argc = len(sys.argv)

    if argc == 2:
        daemon = MyDaemon('/tmp/datagrabber.pid')
        if 'start' == sys.argv[1]:
            print("Starting as daemon.")
            logging.debug("daemon.start()")
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
        else:
            print("Unknown argument %s" % sys.argv[1])
            print("usage: history <asx_code>")

        if result == 0:
            print("Database populated with historic data for %s" % sys.argv[2])
        elif result == 404:
            print("Could not find file for \'%s\'." % sys.argv[2])
            print("Check if code is valid.")
    else:
        print("Not running as daemon!")
        data_grabber.run()

    print("Exiting")