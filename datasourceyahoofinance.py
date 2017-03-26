__author__ = 'jason'

from datasource import DataSource
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


class DatasourceYahoofinance(DataSource):
    def __init__(self, asx_code):
        DataSource.__init__(self, asx_code=asx_code, javascript=True)

    def get_price(self):
        url = "https://au.finance.yahoo.com/q/pr?s=%s.AX" % self.asx_code

        soup = self._get_soup(url=url)
        search_id_string = "yfs_l84_%s.ax" % self.asx_code
        current_price = soup.find(id=search_id_string).get_text()

        return current_price

    def get_historic_data(self):
        # url = "https://au.finance.yahoo.com/q/hp?s=%s.AX" % self.asx_code
        url = "https://au.finance.yahoo.com/quote/%s.AX/history?ltr=1" % self.asx_code
        print(url)
        self.browser.get(url)
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Download data")))
        print("Finished waiting")

        soup = self._get_soup(url=url)

        try:
            file_url = (soup.find_all('a', href=re.compile('^http://chart.finance.yahoo.com/table.csv'))[0].get('href'))
            print("CSV Found!")
        except AttributeError:
            print("Attribute Error: bs4.find() could no1t retrieve text for %s." % self.asx_code)
            print("Check the status of the web page.")
            return None

        return file_url

    def get_key_statistics(self):
        pass