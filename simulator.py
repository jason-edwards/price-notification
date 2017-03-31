__author__ = 'jason'
from trendline import TrendLine
import datetime
import time
import csv
from sqladaptor import DBConnector
from datagrabber import DataGrabber


class Simulator():
    def __init__(self, start_amount, start_date, rules, scrape=False):
        self.current_balance = start_amount
        self.start_date = str_to_date(start_date)
        self.end_date = datetime.datetime.today()
        self.rules = rules
        self.scrape = scrape

        # Format:
        # {asx_code : [{purchase date, qty, unit price}]}
        self.transactions = {}

    def sim_run(self):

        days_in_sec = 60*60*24
        data_grabber = DataGrabber()
        for asx_code in self.rules.asx_code_list:
            if self.scrape:
                # Make sure there is data in the database to build the trendline from.
                data_grabber.historic_data_grab(asx_code)

        all_data = self.build_limits()

        print("Starting simulation.")

        for single_date in range(date_to_int(self.start_date), date_to_int(self.end_date), days_in_sec):
            for asx_code in self.rules.asx_code_list:
                for element in all_data[asx_code]:
                    if element['timestamp'] <= single_date:
                        date_data = element
                        break
                self.sim_buy(date=single_date, asx_code=asx_code, date_data=date_data)
                self.sim_sell(date=single_date, asx_code=asx_code, date_data=date_data)

        for asx_code in self.rules.asx_code_list:
            holdings = 0
            try:
                for transaction in self.transactions[asx_code]:
                    holdings += transaction['quantity']
            except KeyError:
                pass

            print("Stock: %s, %d" % (asx_code, holdings))
        print(self.current_balance)

    def sim_buy(self, date, asx_code, date_data):
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

        price = date_data['price']
        buy_price = date_data['buy_trendline']

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
            buy_qty = int((self.rules.buy_unit-(2*self.rules.transaction_cost))/price)
            equiv_price = float(round((price*buy_qty+2*self.rules.transaction_cost)/buy_qty, 2))
            self.current_balance -= equiv_price*buy_qty

            try:
                self.transactions[asx_code].append({'purchase_date': date, 'quantity': buy_qty, 'unit_price': equiv_price})
            except KeyError:
                print("No previous transactions for %s." % asx_code)
                self.transactions[asx_code] = [{'purchase_date': date, 'quantity': buy_qty, 'unit_price': equiv_price}]


            print("BUY:", asx_code, self.transactions[asx_code][-1], buy_price, price)
            print(self.current_balance)

    def sim_sell(self, date, asx_code, date_data):
        # Conditions:
        # 1. When the current price is higher than the sell trend line
        # 2. When the current price is higher than the minimum profit
        # .
        # .

        bool_sell = False
        temp_bool_sell = False


        price = date_data['price']
        sell_price = date_data['sell_trendline']

        # Condition 1
        if price > sell_price:
            bool_sell = True

        # Condition 2
        profit_multiplier = 1.0 + self.rules.pcent_min_profit
        try:
            for index, element in enumerate(self.transactions[asx_code]):
                if sell_price > element['unit_price']*profit_multiplier:
                    temp_bool_sell = True
                    break
                else:
                    temp_bool_sell = False
        except KeyError:
            print("No previous transactions for %s." % asx_code)

        bool_sell = bool_sell and temp_bool_sell

        if bool_sell:
            item = self.transactions[asx_code].pop(index)
            print("SELL:", asx_code, date, price, element['purchase_date'], element['unit_price'])
            self.current_balance += item['quantity']*price

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
            query_list = []
            print('Building query for %s' % asx_code)
            # Loop through data points from self.start_date to the end_date.
            # For each of these data points, calculate a trendline and corresponding trend point.
            for data_point in query:
                query_list.append({'asx_code': data_point.asx_code,
                                   'price': float(data_point.price),
                                   'timestamp': date_to_int(data_point.timestamp)})

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
                if len(trend_query) > 0:
                    trend_value = TrendLine(date_list, price_list).\
                        get_trend_point(trend_query[0]['timestamp'])
                    trendline.append(trend_value)
                    buy_trendline.append((1.0-self.rules.pcent_buy_lim)*trend_value)
                    sell_trendline.append((1.0+self.rules.pcent_sell_lim)*trend_value)
            print('Trendlines built, writing to csv.')

            csvfile_name = "trend_data.csv"
            with open(csvfile_name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["Code", "Date", "Price", "Trend Point", "Buy Point", "Sell Point"])
                for i in range(0, len(trendline)):
                    price = query_list[i]['price']
                    writer.writerow([asx_code, int_to_excel(time_range_list[i][0]), price,
                                     trendline[i], buy_trendline[i], sell_trendline[i]])
                    code_data.append({'timestamp': time_range_list[i][0], 'price': price,
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
            for j in range(i, query_list_len):
                timestamp_data_point = query_list[i]['timestamp']
                timestamp_comparator = query_list[j]['timestamp']
                timestamp_min = timestamp_data_point - trend_size

                if timestamp_comparator >= timestamp_min:
                    try:
                        time_range_list[i] = [timestamp_comparator, timestamp_data_point]
                        time_index_range_list[i] = [i, j]
                    except IndexError:
                        time_range_list.append([timestamp_comparator, timestamp_data_point])
                        time_index_range_list.append([i, j])
                if timestamp_comparator < timestamp_min:
                    break

        return time_range_list, time_index_range_list




class Rules():
    def __init__(self, asx_code_list=None, pcent_sell_lim=0.05, pcent_buy_lim=0.05,
                 buy_cooldown=90, buy_unit=4000, trend_size=120, pcent_min_profit=0.07,
                 transaction_cost=20):

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


def str_to_date(time_value):
    if type(time_value) is not datetime:
        try:
            time_value = datetime.datetime.strptime(time_value, "%Y-%m-%d")
        except TypeError:
            time_value = time_value.replace(hour=0, minute=0, second=0, microsecond=0)
    return time_value


# Returns a date (str or datetime) as seconds, the reverse of this is datetime.datetime.fromtimestamp(timestamp)
def date_to_int(time_value):
    time_value = str_to_date(time_value)
    time_tpl = time_value.timetuple()
    return int(time.mktime(time_tpl))


def date_to_excel(date1):
    if type(date1) is not datetime:
        try:
            date1 = datetime.datetime.strptime(date1, "%Y-%m-%d")
        except TypeError:
            date1 = date1.replace(hour=0, minute=0, second=0, microsecond=0)
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

if __name__ == "__main__":
    # code_list = ['cba', 'wow', 'wbc', 'tls', 'bhp', 'rio']
    # code_list = ['cba', 'wow']
    # code_list = ['cba']


    with open('asx_code_list.csv', 'r') as f:
        reader = csv.reader(f)
        file_list = list(reader)

    code_list = []
    for code in file_list:
        code_list.append(code[0])

    rules = Rules(asx_code_list=code_list)
#    rules = Rules(asx_code_list=code_list)

    #sim = Simulator(start_amount=1000000, start_date="2000-01-01", rules=rules, scrape=True)
    sim = Simulator(start_amount=100000, start_date="2000-01-01", rules=rules)

#    sim = Simulator(start_amount=40000, start_date="2017-01-01", rules=rules)
    sim.sim_run()