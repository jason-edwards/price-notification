__author__ = 'jason'

# from datagrabber import DataGrabber
# from sqladaptor import DBConnector
from daemon import Daemon
from smtpadaptor import EmailConnector
# from simulator import Simulator, Rules
from simulator import *
import threading
# import time
# import csv
import sys
# import datetime
#import platform

DATAGRAB_SLEEP_TIME = 10  # seconds between each round of data grabbing
datagrab_thread = None
PATH = '/Users/jason/price-notification/'

class DataGrabThread(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.keep_running = True

    def run(self):

        asx_codes_array = ["anz", "cba", "wbc", "cim"]
        #asx_codes_array = ["cba"]
        self.data_grabber = DataGrabber()
        print("Starting datagrab thread loop. This message should only appear once.")
        print(self.keep_running)
        while self.keep_running:
            seconds = 0
            for asx_code in asx_codes_array:
                print("Executing datagrab(" + asx_code + ") in main")
                self.data_grabber.data_grab(asx_code)
            print("Sleeping.")
            while seconds < DATAGRAB_SLEEP_TIME and self.keep_running:
                time.sleep(1)
                seconds += 1
        self.data_grabber.cleanup()


class MyDaemon(Daemon):
    def run(self):
        global datagrab_thread
        datagrab_thread = DataGrabThread()
        datagrab_thread.start()
        app.run(host='0.0.0.0', port=WEB_PORT)


def decision_maker():
    # with open(PATH +'asx_code_list_full.csv', 'r') as f:
    with open(PATH +'asx_code_list.csv', 'r') as f:
        reader = csv.reader(f)
        file_list = list(reader)

    code_list = []
    for code in file_list:
        code_list.append(code[0])

    code_list = code_list
    code_list = ["BHP", "CBA", "TLS", "WOW", "WBC", "ANZ"]

    # decision_data_grabber = DataGrabber()

    # for code in code_list:
    #    decision_data_grabber.data_grab(code)

    # rules = Rules(asx_code_list=code_list)
    rules = Rules(asx_code_list=code_list)

    datetime_today = datetime.datetime.today()
    str_today = datetime_today.strftime("%d/%m/%y %H:%M")
    today = date_to_int(datetime_today)

    with open(PATH + 'Holdings.csv', 'r') as f:
        reader = csv.reader(f)
        file_list = list(reader)

    transactions = {}
    for line in file_list[1:]:
        action = line[0]
        if action == "BUY":
            print("action:", action)
            asx_code = line[1]
            print("code:", asx_code)
            date = date_to_int(line[2])
            print("date:", date)
            buy_qty = int(line[3])
            print("qty:", buy_qty)
            equiv_price = float(line[4])
            print("price:", equiv_price)
            try:
                transactions[asx_code].append({'purchase_date': date, 'quantity': buy_qty,
                                               'unit_price': equiv_price})
            except KeyError:
                transactions[asx_code] = [{'purchase_date': date, 'quantity': buy_qty,
                                           'unit_price': equiv_price}]
    balance = float(line[9])

    sim = Simulator(start_amount=balance, start_date="1997-01-01", rules=rules, scrape=False, transactions=transactions)

    db_instance = DBConnector()
    query = db_instance.get_max_date_records()
    query_data = {}
    for record in query:
        query_data[record.asx_code] = [record.timestamp, record.price]

    all_data = sim.build_limits()

    trasactions_file_name = PATH + 'transactions_%s.csv' % datetime.datetime.today()
    with open(trasactions_file_name, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',
                            quotechar='|', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["Action", "Code", "Action Date", "Action Qty", "Action Price", "Price Limit",
                         "Cur. Price", "Buy Date", "Buy Price", "Balance"])
        for line in file_list[1:]:
            writer.writerow(line)
        csvfile.close()

    for asx_code in sim.rules.asx_code_list:
        element = all_data[asx_code][0]
        date = element['timestamp']

        print(asx_code)
        print(element)
        data = sim.sim_sell(date=date, asx_code=asx_code, code_data=element)

        print(data)
        if data is None:
            data = sim.sim_buy(date=date, asx_code=asx_code, code_data=element)
            print(data)
        if data is not None:
            with open(trasactions_file_name, 'a', newline='') as fp:
                a = csv.writer(fp, delimiter=',')
                a.writerows(data)

    subject = "ASX200 Guide %s" % str_today
    text = "Transaction list for %s." % str_today

    print(trasactions_file_name)

    email = EmailConnector()
    email.send_mail(subject=subject, text=text, files=[trasactions_file_name])

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
        elif 'test' == sys.argv[1]:
            # sim_tester()
            decision_maker()
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
        decision_maker()
        # print("Not running as daemon!")
        # datagrab_thread = DataGrabThread()
        # datagrab_thread.start()


    if datagrab_thread is not None:
        print("Waiting for datagrab thread")
        #datagrab_thread.keep_running = False
        datagrab_thread.join()

print("Exiting")