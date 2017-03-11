__author__ = 'jason'
from trendline import TrendLine
import datetime
import time
from sqladaptor import DBConnector
from datagrabber import DataGrabber

class Simulator():
    def __init__(self, start_amount, start_date, rules):
        self.start_amount = start_amount
        self.start_date = start_date
        self.rules = rules

    def build_limits(self):
        end_date = datetime.datetime.today()
        data_grabber = DataGrabber()
        db_instance = DBConnector()

        for asx_code in self.rules.asx_code_list:
            # Make sure there is data in the database to build the trendline from.
            data_grabber.historic_data_grab(asx_code)

            query = db_instance.\
                get_pricelog_record(code=asx_code,
                                    start_time=self.start_date, end_time=end_date)

            trendline = []

            # Ignore trendlines that do not have enough datapoints. 1/2 trend size is chosen since
            # the worst case scenario for a trend would be Friday - Monday over a weekend.
            if query.count() > (self.rules.trend_size/2):
                for data_point in query:
                    trend_end_date = data_point.timestamp
                    trend_start_date = trend_end_date - self.rules.trend_size
                    trend_query = db_instance.get_pricelog_record(
                        code=asx_code, start_time=trend_start_date, end_time=trend_end_date)

                    date_list = []
                    price_list = []
                    for trend_data_point in trend_query:
                        date_list.append(date_to_int(trend_data_point.timestamp))
                        price_list.append(trend_data_point.price)
                    trend_value = TrendLine(date_list, price_list).\
                        get_trend_point(date_to_int(data_point.timestamp))
                    trendline.append(trend_value)


class Rules():
    def __init__(self, asx_code_list=None, pcent_upper_lim=0.04, pcent_lower_lim=0.04,
                 buy_cooldown=15, buy_unit=4000, trend_size=120, pcent_min_profit=0.04):

        if asx_code_list is None:
            self.asx_code_list = ["cba"]
        else:
            self.asx_code_list = asx_code_list

        self.pcent_upper_lim = pcent_upper_lim
        self.pcent_lower_lim = pcent_lower_lim
        self.pcent_min_profit = pcent_min_profit
        self.buy_cooldown = buy_cooldown
        self.buy_unit = buy_unit
        self.trend_size = trend_size


def datetime_converter(time_value):
    if type(time_value) is not datetime:
        try:
            time_value = datetime.datetime.strptime(time_value, "%Y-%m-%d")
        except TypeError:
            time_value = time_value.replace(hour=0, minute=0, second=0, microsecond=0)
    return time_value


def date_to_int(time_value):
    time_value = datetime_converter(time_value)
    time_tpl = time_value.timetuple()
    return time.mktime(time_tpl)


if __name__ == "__main__":
    rules = Rules()
    sim = Simulator(start_amount=4000, start_date="2000-01-01", rules=rules)
    sim.build_limits()