__author__ = 'jason'
from trendline import TrendLine
import datetime
import time
import csv
from sqladaptor import DBConnector
from datagrabber import DataGrabber

PATH = '/Users/jason/price-notification/'

class Simulator():
    def __init__(self, start_amount, start_date, rules, scrape=False, transactions=None):
        self.current_balance = start_amount
        self.start_date = str_to_date(start_date)
        self.int_start_date = date_to_int(self.start_date)
        self.end_date = datetime.datetime.today()
        self.int_end_date = date_to_int(self.end_date)
        self.int_date_range_end = self.int_end_date + 60*60*24
        self.rules = rules
        self.scrape = scrape

        # Format:
        # {asx_code : [{purchase date, qty, unit price}]}
        if transactions is None:
            self.transactions = {}
        else:
            self.transactions = transactions
    def sim_run(self):

        days_in_sec = 60*60*24

        if self.scrape:
            data_grabber = DataGrabber()
            for asx_code in self.rules.asx_code_list:
                # Make sure there is data in the database to build the trendline from.
                data_grabber.historic_data_grab(asx_code)
#                success = data_grabber.historic_data_grab(asx_code)
#                if success is False:
#                    asx_index = self.rules.asx_code_list.index(asx_code)
#                    self.rules.asx_code_list.pop(asx_index)

        all_data = self.build_limits()

        print("Starting simulation.")
        with open(PATH + 'transactions.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["Action", "Code", "Action Date", "Action Qty", "Action Price", "Price Limit",
                             "Cur. Price", "Buy Date", "Buy Price", "Balance"])
            csvfile.close()

        for single_date in range(date_to_int(self.start_date), date_to_int(self.end_date)+days_in_sec, days_in_sec):
            for asx_code in self.rules.asx_code_list:
                for element in all_data[asx_code]:
                    if element['timestamp'] <= single_date:
                        self.sim_sell(date=single_date, asx_code=asx_code, code_data=element)
                        self.sim_buy(date=single_date, asx_code=asx_code, code_data=element)
                        break

        for asx_code in self.rules.asx_code_list:
            holdings = 0
            try:
                for transaction in self.transactions[asx_code]:
                    holdings += transaction['quantity']
            except KeyError:
                pass
            print("Stock: %s, %d" % (asx_code, holdings))

        with open(PATH + 'final_holdings.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            writer.writerow(["Code", "Purchase Date", "Qty", "Equiv Price"])

            for asx_code, value in self.transactions.items():
                for transaction in value:
                    writer.writerow([asx_code, int_to_excel(transaction['purchase_date']),
                                     transaction['quantity'], transaction['unit_price']])

        print(self.current_balance)

    def sim_buy(self, date, asx_code, code_data):
        # Conditions:
        # 1. When the current price is less than the buy trend line
        # 2. current_balance - buy_unit must be positive
        # 3. The last purchase wasn't within the cooldown period.
        #   3a. The cooldown period is overwritten if the current price is
        #       less than the buy trend line * (1 - pcent_buy_lim)
        # 4.
        # .
        # For each day of the year cycle through the list of stock codes and decide if a purchase should be made.

        bool_buy = False
        days_in_sec = 60*60*24

        price = code_data['price']
        buy_price = code_data['buy_trendline']

        # Condition 1
        if price <= buy_price:
            bool_buy = True

        # Condition 2 ($40 in account for transactions)
        if (self.current_balance - self.rules.buy_unit) >= 40:
            bool_buy = bool_buy and True
        else:
            bool_buy = False

        # Condition 3
        cooldown_date = date - self.rules.buy_cooldown*days_in_sec
        #if price <= (buy_price * (1.0 - 2.0*self.rules.pcent_buy_lim)):
        #    bool_buy = bool_buy and True
        #else:
        try:
            for element in self.transactions[asx_code]:
                if cooldown_date <= element['purchase_date']:
                    bool_buy = False
        except KeyError:
            print("No previous transactions for %s." % asx_code)
            self.transactions[asx_code] = []

        if bool_buy:
            if self.current_balance < self.rules.buy_unit_override_price:
                buy_qty = int((self.rules.buy_unit-(2*self.rules.transaction_cost))/price)
            else:
                buy_qty = int((self.current_balance*self.rules.pcent_buy_unit-(2*self.rules.transaction_cost))/price)

            equiv_price = float(round((price*buy_qty+2*self.rules.transaction_cost)/buy_qty, 10))
            self.current_balance -= equiv_price*buy_qty

            try:
                self.transactions[asx_code].append({'purchase_date': date, 'quantity': buy_qty,
                                                    'unit_price': equiv_price})
            except KeyError:
                self.transactions[asx_code] = [{'purchase_date': date, 'quantity': buy_qty,
                                                'unit_price': equiv_price}]

            with open(PATH + 'transactions.csv', 'a', newline='') as fp:
                    a = csv.writer(fp, delimiter=',')
                    data = [["BUY", asx_code, int_to_excel(date), buy_qty, equiv_price, buy_price, price,
                             '', '', self.current_balance]]
                    a.writerows(data)

            print("BUY:", asx_code, self.transactions[asx_code][-1],
                  buy_price, price)
            print(self.current_balance, datetime.datetime.fromtimestamp(date))
            return data
        else:
            return None

    def sim_sell(self, date, asx_code, code_data):
        # Conditions:
        # 1. When the current price is higher than the sell trend line
        # 2. When the current price is higher than the minimum profit
        # 3. If the current holdings has been held for more than a year and the trend
        # 4.

        bool_sell = False
        temp_bool_sell = False
        days_in_sec = 60*60*24

        price = code_data['price']
        sell_price = code_data['sell_trendline']

        # Condition 1
        if price > sell_price:
            bool_sell = True

        # Condition 2
        profit_multiplier = 1.0 + self.rules.pcent_min_profit
        try:
            for index, element in enumerate(self.transactions[asx_code]):
                if price > element['unit_price']*profit_multiplier:
                    temp_bool_sell = True
                    break
                else:
                    temp_bool_sell = False
        except KeyError:
            print("No current holdings for %s." % asx_code)
            return None

        buy_date = int_to_excel(element['purchase_date'])
        buy_price = element['unit_price']
        bool_sell = temp_bool_sell and bool_sell

        if bool_sell:
            sell_details = [asx_code, date, price, index, element, sell_price]
            data = self.sell(sell_details)
            return data
        else:
            pcent_profit = (sell_price - buy_price)/buy_price
            if ((date - buy_date) <= days_in_sec*31) & (pcent_profit > self.rules.pcent_min_profit-0.02):
                    sell_details = [asx_code, date, price, index, element, sell_price]
                    data = self.sell(sell_details)
                    return data

            if (date - buy_date) > days_in_sec*365:
                bisect_date = buy_date + (date - buy_date)/2  # Bisection between the current date and the buy date
                db_instance = DBConnector()
                query = db_instance.\
                    get_pricelog_record(code=asx_code,
                                        start_time=datetime.datetime.fromtimestamp(bisect_date),
                                        end_time=datetime.datetime.fromtimestamp(date))
                query_len = len(query)
                date_list = [None]*query_len
                price_list = [None]*query_len
                print('Building sell query for %s' % asx_code)
                for i in range(query_len):
                    data_point = query[i]
                    date_list[i] = date_to_int(data_point.timestamp)
                    price_list[i] = float(data_point.price),

                trend = TrendLine(date_list, price_list)
                if trend.gradient < 0:
                    sell_details = [asx_code, date, price, index, element, sell_price]
                    data = self.sell(sell_details)
                    return data
            return None

    def sell(self, sell_details):
        try:
            asx_code = sell_details[0]
            date = sell_details[1]
            price = sell_details[2]
            index = sell_details[3]
            element = sell_details[4]
            sell_price = sell_details[5]
        except IndexError:
            print("Problem with sell details")
            return None

        try:
            item = self.transactions[asx_code].pop(index)
        except UnboundLocalError:
            return None
        sell_qty = item['quantity']
        buy_price = element['unit_price']
        buy_date = int_to_excel(element['purchase_date'])
        print("SELL:", asx_code, date, price, buy_date, buy_price)
        self.current_balance += sell_qty*price

        with open(PATH + 'transactions.csv', 'a', newline='') as fp:
            a = csv.writer(fp, delimiter=',')
            data = [["SELL", asx_code, int_to_excel(date), sell_qty, price, sell_price, '',
                     buy_date, buy_price, self.current_balance]]
            a.writerows(data)
        return data

    # Packages details into separate csv files for each stock code
    def build_limits(self):
        end_date = self.end_date
        query_start_date = str_to_date(self.start_date) - datetime.timedelta(days=self.rules.trend_size)

        db_instance = DBConnector()

        all_data = {}
        for asx_code in self.rules.asx_code_list:
            code_data = []

            query = db_instance.\
                get_pricelog_record(code=asx_code,
                                    start_time=query_start_date,
                                    end_time=end_date)

            trendline = []
            buy_trendline = []
            sell_trendline = []
            query_len = len(query)
            query_list = [None]*query_len
            print('Building query for %s' % asx_code)
            # Loop through data points from self.start_date to the end_date.
            # For each of these data points, calculate a trendline and corresponding trend point.
            for i in range(query_len):
                data_point = query[i]
                query_list[i] = {'asx_code': data_point.asx_code,
                                 'price': float(data_point.price),
                                 'timestamp': date_to_int(data_point.timestamp)}

            print('Building date range for %s' % asx_code)

            time_range_list, time_index_range_list = self.build_time_range(query_list)

            print('Building trend lines for %s' % asx_code)

            for indices in time_index_range_list:
                trend_query = query_list[indices[0]:indices[1]]

                date_list = []
                price_list = []
                for trend_data_point in trend_query:
                    date_list.append(trend_data_point['timestamp'])
                    price_list.append(trend_data_point['price'])
                if len(trend_query) > self.rules.trend_size/4:
                    trend_value = TrendLine(date_list, price_list).\
                        get_trend_point(trend_query[0]['timestamp'])
                    trendline.append(trend_value)
                    buy_trendline.append((1.0-self.rules.pcent_buy_lim)*trend_value)
                    sell_trendline.append((1.0+self.rules.pcent_sell_lim)*trend_value)
            print('Trendlines built, writing to csv.')

            csvfile_name = (PATH + "trend_data_%s.csv") % asx_code
            with open(csvfile_name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["Code", "Date", "Price", "Trend Point", "Buy Point", "Sell Point"])
                for i in range(0, len(trendline)):
                    price = query_list[i]['price']
                    date = time_range_list[i][1]
                    writer.writerow([asx_code, int_to_excel(date), price,
                                     trendline[i], buy_trendline[i], sell_trendline[i]])
                    code_data.append({'timestamp': date, 'price': price,
                                      'trendline': trendline[i], 'buy_trendline': buy_trendline[i],
                                      'sell_trendline': sell_trendline[i]})

            all_data[asx_code] = code_data
            print('%s written' % csvfile_name)
        #print(all_data)
        return all_data

    def build_time_range(self, query_list):
        time_range_list = []
        time_index_range_list = []
        query_list_len = len(query_list)
        trend_size = (self.rules.trend_size+1)*60*60*24
        for i in range(0, query_list_len):
            timestamp_data_point = query_list[i]['timestamp']
            timestamp_min = timestamp_data_point - trend_size
            for j in range(i, query_list_len):
                timestamp_comparator = query_list[j]['timestamp']

                if timestamp_comparator >= timestamp_min:
                    try:
                        time_range_list[i] = [timestamp_comparator, timestamp_data_point]
                        time_index_range_list[i] = [i, j]
                    except IndexError:
                        time_range_list.append([timestamp_comparator, timestamp_data_point])
                        time_index_range_list.append([i, j])
                else:
                    break
        return time_range_list, time_index_range_list


class Rules():
    def __init__(self, asx_code_list=None, pcent_sell_lim=0.05, pcent_buy_lim=0.05,
                 buy_cooldown=90, buy_unit=4000, trend_size=120, pcent_min_profit=0.05,
                 transaction_cost=20, buy_unit_override_price=400000, pcent_buy_unit=0.01):

        if asx_code_list is None:
            self.asx_code_list = ["cba"]
        else:
            self.asx_code_list = asx_code_list

        self.pcent_sell_lim = pcent_sell_lim
        self.pcent_buy_lim = pcent_buy_lim
        self.pcent_min_profit = pcent_min_profit
        self.buy_cooldown = buy_cooldown
        self.buy_unit = buy_unit
        self.trend_size = trend_size
        self.transaction_cost = transaction_cost
        self.buy_unit_override_price = buy_unit_override_price
        self.pcent_buy_unit = pcent_buy_unit


def str_to_date(time_value):
    if type(time_value) is not datetime:
        try:
            time_value = datetime.datetime.strptime(time_value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            time_value = datetime.datetime.strptime(time_value, "%Y-%m-%d")
        except TypeError:
            pass
    return time_value


# Returns a date (str or datetime) as seconds, the reverse of this is datetime.datetime.fromtimestamp(timestamp)
def date_to_int(time_value):
    time_value = str_to_date(time_value)
    time_tpl = time_value.timetuple()
    return int(time.mktime(time_tpl))


def date_to_excel(date1):
    if type(date1) is not datetime:
        try:
            date1 = datetime.datetime.strptime(date1, "%Y-%m-%d %H:%M")
        except ValueError:
            date1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
        except TypeError:
            pass
    # temp = datetime.datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
    temp = datetime.datetime(1904, 1, 1)

    delta = date1 - temp
    return float(delta.days) + (float(delta.seconds) / 86400)


def int_to_excel(date1):
    date_str = "2000-01-01"
    date_str1 = "2000-01-02"
    time_scaler = (date_to_int(date_str) - date_to_int(date_str1)) /\
                  (date_to_excel(date_str) - date_to_excel(date_str1))

    time_delta = date_to_int(date_str)/time_scaler - date_to_excel(date_str)
    time_value = date1/time_scaler - time_delta
    return time_value


# Creates a range of days
def daterange(range_start, range_end):
    for n in range(int((range_end - range_start).days)):
        yield range_start + datetime.timedelta(days=n)

def sim_tester():
    with open(PATH + 'asx_code_list.csv', 'r') as f:
        reader = csv.reader(f)
        file_list = list(reader)

    code_list = []
    for code in file_list:
        code_list.append(code[0])

    # code_list = ['cba', 'wow', 'wbc', 'tls', 'bhp', 'rio']
    # code_list = ['wow']
    # code_list = ['cba']
    # code_list = ['ozl']


    # rules = Rules(asx_code_list=code_list)
    rules = Rules(asx_code_list=code_list)

    sim = Simulator(start_amount=100000, start_date="1997-01-01", rules=rules, scrape=True)
    # sim = Simulator(start_amount=100000, start_date="2000-01-01", rules=rules)

    # sim = Simulator(start_amount=40000, start_date="2017-01-01", rules=rules)
    sim.sim_run()

if __name__ == "__main__":

    with open(PATH + 'asx_code_list.csv', 'r') as f:
        reader = csv.reader(f)
        file_list = list(reader)

    code_list = []
    for code in file_list:
        code_list.append(code[0])

    # code_list = ['cba', 'wow', 'wbc', 'tls', 'bhp', 'rio']
    # code_list = ['wow']
    # code_list = ['cba']
    # code_list = ['ozl']


    # rules = Rules(asx_code_list=code_list)
    rules = Rules(asx_code_list=code_list)

    sim = Simulator(start_amount=100000, start_date="1997-01-01", rules=rules, scrape=True)
    # sim = Simulator(start_amount=100000, start_date="2000-01-01", rules=rules)

    # sim = Simulator(start_amount=40000, start_date="2017-01-01", rules=rules)
    sim.sim_run()