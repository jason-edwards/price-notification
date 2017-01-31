__author__ = 'jason'

import datetime
import peewee as pw

DATABASE_USER = 'pricevis'

try:
    f = open(DATABASE_USER + '.passwd', 'r')
    passwd = f.read()[:-1]
except IOError:
    print("Cannot open database password file. Password file should be named <db-user>.passwd")
else:
    f.close()
db = pw.MySQLDatabase('shares_db', host='127.0.0.1', user=DATABASE_USER, password=passwd)


class BaseModel(pw.Model):
    class Meta:
        database = db


class DBConnector():
    def get_pricelog_record(self, code, start_time=None, end_time=None):
        if (start_time is None) and (end_time is None):
            query = (PriceLog
                     .select()
                     .where(PriceLog.asx_code == code)
                     .order_by(PriceLog.timestamp.desc())
                     .get())
        else:
            if end_time is None:
                end_time = datetime.datetime.now()
            elif type(end_time) is not datetime:
                try:
                    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d")
                except TypeError:
                    end_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)

            if start_time is None:
                start_time = end_time - datetime.timedelta(days=90)
            elif type(start_time) is not datetime:
                try:
                    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d")
                except TypeError:
                    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            query = (PriceLog
                     .select()
                     .where((PriceLog.asx_code == code) & (PriceLog.timestamp >= start_time) &
                            (PriceLog.timestamp <= end_time))
                     .order_by(PriceLog.timestamp.desc()))
        return query


class PriceLog(BaseModel):
    id = pw.PrimaryKeyField()
    asx_code = pw.CharField()
    price = pw.DecimalField()
    timestamp = pw.DateTimeField()