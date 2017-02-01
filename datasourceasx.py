__author__ = 'jason'

from datasource import DataSource


class DataSourceASX(DataSource):
    def __init__(self, asx_code):
        DataSource.__init__(self, asx_code=asx_code, javascript=True)

    def get_price(self):
        url = "http://search.asx.com.au/s/search.html?query=%s&collection=asx-meta&profile=web" % self.asx_code

        soup = self._get_soup(url=url)

        try:
            prices_table = soup.find("table").find("tbody")
            current_price = prices_table.find_all("td")[0].get_text()
        except AttributeError:
            print("\tUnable to scrape this time.")
            return None

        return current_price

    def get_historic_data(self):
        """
        No known place to retrieve historical data from the www.asx.com.au
        """