__author__ = 'jason'

import smtplib
import datetime
from sqladaptor import PriceLog, DBConnector

MAIL_USER = 'jedwards'

class EmailConnector():
    def __init__(self):
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
        mail_server.login("jedwards@live.com.au", password=passwd)
        mail_server.close()

if __name__ == "__main__":
    email = EmailConnector()