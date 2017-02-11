__author__ = 'jason'

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import platform
import requests as req
from bs4 import BeautifulSoup

class DataSource():
    def __init__(self, asx_code, javascript=True):
        if javascript:
            if platform.system() != "Darwin":
                self.browser = webdriver.PhantomJS('./phantomjs')
            else:
                self.browser = webdriver.PhantomJS()
        else:
            self.browser = None
        self.javascript_enabled = javascript
        self.asx_code = asx_code

    def clean_up(self):
        self.browser.close()

    def _get_soup(self, url):

        if self.javascript_enabled:
            try:
                self.browser.get(url)
                WebDriverWait(self.browser, 10).until(
                    EC.presence_of_element_located((By.ID, "aaaaacompany_details_widget_form:company_details_widget_results"))
                )
                print("Finished waiting")
            except:
                raise LookupError()

            self.browser.execute_script("return document.cookie")
            self.browser.execute_script("return navigator.userAgent")
            html_source = self.browser.page_source
        else:
            page = req.get(url)
            html_source = page.text

        return BeautifulSoup(html_source, "html.parser")

    def get_price(self):
        """
        Placeholder function: to be overwritten by subclass.
        """

    def get_key_statistics(self):
        """
        Placeholder function: to be overwritten by subclass.
        """

    def get_historic_data(self):
        """
        Placeholder function: to be overwritten by subclass.
        """
