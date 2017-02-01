__author__ = 'jason'

from datasource import DataSource
import re


class DatasourceYahoofinance(DataSource):
    def __init__(self, asx_code):
        DataSource.__init__(self, asx_code=asx_code, javascript=False)

    def get_price(self):
        url = "https://au.finance.yahoo.com/q/pr?s=%s.AX" % self.asx_code

        soup = self._get_soup(url=url)
        search_id_string = "yfs_l84_%s.ax" % self.asx_code
        current_price = soup.find(id=search_id_string).get_text()

        return current_price

    def get_historic_data(self):
        url = "https://au.finance.yahoo.com/q/hp?s=%s.AX" % self.asx_code

        soup = self._get_soup(url=url)
        search_id_string = 'rightcol'

        try:
            file_url = (soup.find(id=search_id_string)
                        .find_all('a', href=re.compile('^http://real-chart.finance'))[0].get('href'))
        except AttributeError:
            print("Attribute Error: bs4.find() could no1t retrieve text for %s." % self.asx_code)
            print("Check the status of the web page.")
            return None

        return file_url

    def get_key_statistics(self):
        pass