__author__ = 'jason'

import smtplib
import datetime
from sqladaptor import PriceLog, DBConnector
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

PATH = '/Users/jason/price-notification/'
MAIL_USER = 'jedwards'
MAIL_DOMAIN = '@live.com.au'

class EmailConnector():
    def send(self, message):
        try:
            f = open(PATH + MAIL_USER + '.passwd', 'r')
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

        print(message)

        mail_server.sendmail(MAIL_USER + MAIL_DOMAIN, "jedwards@live.com.au", message)

        mail_server.close()

    def send_mail(self, subject, text, files=None):
        try:
            f = open(PATH + MAIL_USER + '.passwd', 'r')
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

        msg = MIMEMultipart()
        msg['From'] = MAIL_USER + MAIL_DOMAIN
        msg['To'] = MAIL_USER + MAIL_DOMAIN
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject

        msg.attach(MIMEText(text))

        for f in files or []:
            with open(f, "rb") as fil:
                part = MIMEApplication(
                    fil.read(),
                    Name=basename(f)
                )
                part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
                msg.attach(part)
        print(MAIL_USER + MAIL_DOMAIN)

        mail_server.sendmail(MAIL_USER + MAIL_DOMAIN, "jedwards@live.com.au", msg.as_string())
        mail_server.close()

if __name__ == "__main__":
    email = EmailConnector()