__author__ = 'jason'
from trendline import TrendLine
import datetime
import time
import csv
from sqladaptor import DBConnector
from datagrabber import DataGrabber


class Simulator():
    def __init__(self, start_amount, start_date, rules):
        self.current_balance = start_amount
        self.start_date = str_to_date(start_date)
        self.rules = rules

    def sim_run(self):
        self.build_limits()
        self.sim_buy()

    def sim_buy(self):
        # Conditions:
        # 1. When the current price is less than the buy trend line
        # 2. current_balance must be positive
        # 3. The last purchase wasn't within the cooldown period.
        #   3a. The cooldown period is overwritten if the current price is
        #       less than the buy trend line * (1 - pcent_buy_lim)
        # 4.

        bool_buy = True






        pass

    def build_limits(self, asx_code):
        end_date = datetime.datetime.today()
        query_start_date = str_to_date(self.start_date) - datetime.timedelta(days=self.rules.trend_size)
        data_grabber = DataGrabber()
        db_instance = DBConnector()

        all_data = []
        for asx_code in self.rules.asx_code_list:
            # Make sure there is data in the database to build the trendline from.
            data_grabber.historic_data_grab(asx_code)

            query = db_instance.\
                get_pricelog_record(code=asx_code,
                                    start_time=query_start_date,
                                    end_time=end_date)

            trendline = []
            buy_trendline = []
            sell_trendline = []
            query_list = []
            print('Sorting data for %s' % asx_code)
            # Loop through data points from self.start_date to the end_date.
            # For each of these data points, calculate a trendline and corresponding trend point.
            for data_point in query:
                query_list.append({'asx_code': data_point.asx_code,
                                   'price': data_point.price,
                                   'timestamp': data_point.timestamp})

            time_range_list = []
            time_index_range_list = []
            for i in range(0, len(query_list)):
                for j in range(i, len(query_list)):
                    if query_list[j]['timestamp'] >=\
                            query_list[i]['timestamp'] -\
                            datetime.timedelta(days=(self.rules.trend_size+1)):
                        try:
                            time_range_list[i] = [query_list[i]['timestamp'], query_list[j]['timestamp']]
                            time_index_range_list[i] = [i, j]
                        except IndexError:
                            time_range_list.append([query_list[i]['timestamp'], query_list[j]['timestamp']])
                            time_index_range_list.append([i, j])
                    if query_list[j]['timestamp'] <\
                            query_list[i]['timestamp'] -\
                            datetime.timedelta(days=(self.rules.trend_size+1)):
                        break
            print('Building trend lines for %s' % asx_code)

            for indices in time_index_range_list:
                trend_query = query_list[indices[0]:indices[1]]

                date_list = []
                price_list = []
                for trend_data_point in trend_query:
                    date_list.append(date_to_int(trend_data_point['timestamp']))
                    price_list.append(trend_data_point['price'])
                if len(trend_query) > 0:
                    trend_value = TrendLine(date_list, price_list).\
                        get_trend_point(date_to_int(trend_query[0]['timestamp']))
                    trendline.append(trend_value)
                    buy_trendline.append((1.0-self.rules.pcent_buy_lim)*trend_value)
                    sell_trendline.append((1.0+self.rules.pcent_sell_lim)*trend_value)
            print('Trendlines built, writing to csv.')

            csvfile_name = "trend_data_%s.csv" % asx_code
            with open(csvfile_name, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(["Date", "Price", "Trend Point", "Buy Point", "Sell Point"])
                for i in range(0, len(trendline)):
                    price = query_list[i]['price']
                    writer.writerow([date_to_excel(time_range_list[i][0]), price,
                                     trendline[i], buy_trendline[i], sell_trendline[i]])
                all_data.append({'asx_code': asx_code, 'timestamp': time_range_list[i][0],
                                'price': price, 'trendline': trendline[i], 'buy_trendline': buy_trendline[i],
                                'sell_trendline': sell_trendline[i]})

            print('%s written/r/n' % csvfile_name)


class Rules():
    def __init__(self, asx_code_list=None, pcent_sell_lim=0.04, pcent_buy_lim=0.04,
                 buy_cooldown=15, buy_unit=4000, trend_size=120, pcent_min_profit=0.04):

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


def str_to_date(time_value):
    if type(time_value) is not datetime:
        try:
            time_value = datetime.datetime.strptime(time_value, "%Y-%m-%d")
        except TypeError:
            time_value = time_value.replace(hour=0, minute=0, second=0, microsecond=0)
    return time_value


def date_to_int(time_value):
    time_value = str_to_date(time_value)
    time_tpl = time_value.timetuple()
    return time.mktime(time_tpl)


def date_to_excel(date1):
    temp = datetime.datetime(1899, 12, 30)    # Note, not 31st Dec but 30th!
    delta = date1 - temp
    return float(delta.days) + (float(delta.seconds) / 86400)


if __name__ == "__main__":
    code_list = ['cba', 'wow', 'wbc', 'tls', 'bhp']
    rules = Rules(asx_code_list=code_list)
    sim = Simulator(start_amount=4000, start_date="2000-01-01", rules=rules)
    sim.build_limits()