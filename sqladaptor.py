__author__ = 'jason'

import datetime
import peewee as pw
#from playhouse.shortcuts import RetryOperationalError



#class MyRetryDB(RetryOperationalError, pw.MySQLDatabase):
#    pass

PATH = '/Users/jason/price-notification/'
DATABASE_USER = 'pricevis'

try:
    f = open(PATH + DATABASE_USER + '.passwd', 'r')
    passwd = f.read()[:-1]
except IOError:
    print("Cannot open database password file. Password file should be named <db-user>.passwd")
else:
    f.close()

try:
#    db = MyRetryDB('shares_db',
#                    host='52.24.137.82',
#                    user=DATABASE_USER,
#                    password=passwd)
    db = pw.MySQLDatabase('shares_db',
                          host='52.24.137.82',
                          user=DATABASE_USER,
                          password=passwd,
                          max_allowed_packet=64*1024*1024)
    db.connect()
except Exception as e:
    print(e)


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
                    end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)

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

    def get_max_date_records(self):
        # When referencing a table multiple times, we'll call Model.alias() to create
        # a secondary reference to the table.
        pricelog_alias = PriceLog.alias()

        # Create a subquery that will calculate the maximum timestamp for each
        # code.
        subquery = (pricelog_alias
                    .select(
                        pricelog_alias.asx_code,
                        pw.fn.MAX(pricelog_alias.timestamp).alias('max_ts'))
                    .group_by(pricelog_alias.asx_code)
                    .alias('log_max_subquery'))

        # Query for posts and join using the subquery to match the post's user
        # and timestamp.
        query = (PriceLog
                 .select(PriceLog)
                 .join(subquery, on=(
                     (PriceLog.timestamp == subquery.c.max_ts) &
                     (PriceLog.asx_code == subquery.c.asx_code))))

        return query


class PriceLog(BaseModel):
    id = pw.PrimaryKeyField()
    asx_code = pw.CharField()
    price = pw.DecimalField()
    timestamp = pw.DateTimeField()