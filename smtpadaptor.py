__author__ = 'jason'

import smtplib
import datetime
from sqladaptor import PriceLog, DBConnector

MAIL_USER = 'jedwards'
MAIL_DOMAIN = '@live.com.au'

class EmailConnector():
    def __init__(self):
        db_instance = DBConnector()

        try:
            f = open(MAIL_USER + '.passwd', 'r')
            passwd = f.read()[:-1]
        except IOError:
            print("Cannot open database password file. Password file should be named <db-user>.passwd")
        else:
            f.close()

        mail_server = smtplib.SMTP("smtp.live.com", 587)
        mail_server.set_debuglevel(True)
        mail_server.ehlo()
        mail_server.starttls()
        mail_server.ehlo()
        mail_server.login(MAIL_USER + MAIL_DOMAIN, password=passwd)

        query_result = db_instance.get_pricelog_record(code="cba")

        pricelog = PriceLog(id=query_result.id,
                            asx_code=query_result.asx_code,
                            price=query_result.price,
                            timestamp=query_result.timestamp)

        message = "ID: " + str(pricelog.id) + \
                  "\r\nASX Code: " + pricelog.asx_code + \
                  "\r\nPrice: " + str(pricelog.price) + \
                  "\r\nTimestamp: " + str(pricelog.timestamp)

        print(message)

        mail_server.sendmail(MAIL_USER + MAIL_DOMAIN, "shalvin.deo@live.com", message)

        mail_server.close()

if __name__ == "__main__":
    email = EmailConnector()