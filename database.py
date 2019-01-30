from abc import ABCMeta, abstractmethod, abstractproperty
import pymongo
import psycopg2 as ps
import datetime


class Repository():
    __metaclass__ = ABCMeta

    @abstractmethod
    def write_data(self, data):
        pass

    @abstractmethod
    def get_data_today(self):
        pass

    @abstractmethod
    def get_currency(self, currency):
        pass

    @abstractproperty
    def database(self):
        pass


class MongoRepository(Repository):
    database = None

    def __init__(self):
        conn = pymongo.MongoClient()
        self.database = conn['exchange_rate']

    def write_data(self, data):
        collection = self.database['currency']

        actual_date = data[0]['Date']
        # actual_date = datetime.datetime.strftime(datetime.datetime.now(), "%d.%m.%Y")

        count = 0

        for _ in collection.find({'Date': actual_date}):
            count += 1

        if count == 0:
            posts = collection.insert_many(data)
            print('Collection write')
        else:
            print('Collection exist')

        return

    def get_data_today(self):
        collection = self.database['currency']

        # actual_date = datetime.datetime.strftime(datetime.datetime.now(), "%d.%m.%Y")
        actual_date = '26.01.2019'

        docs = list()

        for doc in collection.find({'Date': actual_date}):
            docs.append(doc)

        pipeline = [
            {'$group': {
                '_id': "$CharCode",
                'Average': {'$avg': '$Value'} } } ]

        avg = list(collection.aggregate(pipeline=pipeline))

        return docs, avg

    def get_currency(self, currency):
        collection = self.database['currency']

        docs = list()

        for doc in collection.find({'CharCode': currency}):
            docs.append(doc)

        return docs


class PostgresRepository(Repository):
    database = None

    def __init__(self):
        self.database = ps.connect("user = 'ksenia' password = 'KseniaB0908' dbname = 'exchange_rate'")

    def write_data(self, data):
        cursor = self.database.cursor()

        cursor.execute("SELECT * FROM information_schema.tables WHERE  table_name = 'exchange_rate'")

        if cursor.rowcount != 0:
            print("DB Already exists")
        else:
            cursor.execute("CREATE TABLE exchange_rate (Date varchar(20), Name varchar, CharCode varchar(10), Value double precision);")
            self.database.commit()
            print('Create')

        actual_date = data[0]['Date']

        cursor.execute("SELECT exchange_rate.date FROM exchange_rate WHERE exchange_rate.date = %s", (actual_date,))

        if cursor.rowcount != 0:
            print('Data exist!')
        else:
            cursor.executemany("""INSERT INTO exchange_rate(date, name, charcode, value) VALUES(%(Date)s, %(Name)s, %(CharCode)s, %(Value)s)""", data)
            self.database.commit()
            print('Data write!')

        self.database.close()

        return

    def get_data_today(self):
        cursor = self.database.cursor()

        actual_date = datetime.datetime.strftime(datetime.datetime.now(), "%d.%m.%Y")
        # actual_date = '25.01.2019'

        cursor.execute("SELECT exchange_rate.date, exchange_rate.name, exchange_rate.charcode, exchange_rate.value, AVG(exchange_rate.value) "
                       "FROM exchange_rate "
                       "WHERE exchange_rate.date = %s "
                       "GROUP BY exchange_rate.date, exchange_rate.name, exchange_rate.charcode, exchange_rate.value", (actual_date,))
        tables = cursor.fetchall()

        return tables

    def get_currency(self, currency):
        cursor = self.database.cursor()

        cursor.execute("SELECT * FROM exchange_rate WHERE exchange_rate.charcode = %s", (currency,))
        tables = cursor.fetchall()

        return tables
