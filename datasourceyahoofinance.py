__author__ = 'jason'

from datasource import DataSource
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from time import sleep
import datetime
import re



class DatasourceYahoofinance(DataSource):
    def __init__(self, asx_code):
        DataSource.__init__(self, asx_code=asx_code, javascript=True)

    def get_price(self):

        return None

        url = "https://au.finance.yahoo.com/quote/%s.AX/" % self.asx_code

        self.browser.get(url)

        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.ID, "defaultLREC-wrapper")))

        soup = self._get_soup(url=url)


        try:
            # search_id_string = "yfs_l84_%s.ax" % self.asx_code
            print(soup.title.get_text())
            current_price = soup.find(attrs={"data-reactid": "259"}).get_text()
        except AttributeError:
            print("\tUnable to scrape YahooFinance.com this time.")
            return None

        return current_price

    def get_historic_data(self):

        period1 = 0
        dt_period2 = datetime.datetime.today() - datetime.datetime(1970, 1, 1)
        int_period2 = dt_period2.seconds + dt_period2.days*24*60*60

        url = "https://au.finance.yahoo.com/quote/%s.AX/history" \
              "?period1=%d&period2=%d&interval=1d&filter=history&frequency=1d" \
              % (self.asx_code, period1, int_period2)

        self.browser.get(url)
        url = self.browser.current_url
        print(url)

        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[starts-with(@href, 'http://chart.finance.yahoo.com/table.csv')]")))

        soup = self._get_soup(url=url)

        try:
            file_url = (soup.find_all('a', href=re.compile('^http://chart.finance.yahoo.com/table.csv'))[0].get('href'))
            print("CSV Found!")
        except AttributeError:
            print("Attribute Error: bs4.find() could no1t retrieve text for %s." % self.asx_code)
            print("Check the status of the web page.")
            return None
        except TimeoutError:
            return False

        return file_url

    def get_key_statistics(self):
        pass