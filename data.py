from flask import Flask, render_template, jsonify
import requests
import xmltodict
import working_with_database as db
import datetime
import time
import yaml

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)

database = cfg['database']

app = Flask(__name__)


def write_to_database(database_name: str):
    content = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')

    xpars = dict(xmltodict.parse(content.text))

    data = list()

    for val in xpars['ValCurs']['Valute']:
        currency = dict()
        currency['Date'] = xpars['ValCurs']['@Date']
        currency['CharCode'] = val['CharCode']
        currency['Name'] = val['Name']
        currency['Value'] = float(val['Value'].replace(',', '.'))
        data.append(currency)

    if database_name == 'mongodb':
        element = db.MongoRepository()
        element.write_data(data)
    elif database_name == 'postgres':
        element = db.PostgresRepository()
        element.write_data(data)

    return


def get_from_database(database_name: str):
    if database_name == 'mongodb':
        element = db.MongoRepository()
        data = element.get_data_today()
    elif database_name == 'postgres':
        element = db.PostgresRepository()
        data = element.get_data_today()

    return data


def get_currency(database_name: str, key: str):
    if database_name == 'mongodb':
        element = db.MongoRepository()
        data = element.get_currency(key)
    elif database_name == 'postgres':
        element = db.PostgresRepository()
        data = element.get_currency(key)

    return data

@app.route('/')
def actions():

    if database == 'mongodb':
        write_to_database(database)
        array = get_from_database(database)

        data_currency = list()
        charcode = list()

        for d in array[1]:
            for val in array[0]:
                if val['CharCode'] == d['_id']:
                    val['Average'] = round(d['Average'], 4)
        data = array[0]

        for val in array[0]:
            name = val['CharCode']
            charcode.append([name])
            cur = get_currency(database, name)
            arr = list()
            for i in cur:
                arr.append(i['Value'])
            val['Data_cur'] = ', '.join(str(v) for v in arr)
            # val['Data_cur'] = arr
            data_currency.append(arr)


    elif database == 'postgres':
        write_to_database(database)
        value = get_from_database(database)

        data = list()

        for i in value:
            currency = dict()
            currency['Date'] = i[0]
            currency['Name'] = i[1]
            currency['CharCode'] = i[2]
            currency['Value'] = i[3]
            currency['Average'] = i[4]
            data.append(currency)

    time = datetime.datetime.strftime(datetime.datetime.now(), "%d.%m.%Y")

    return render_template('index.html', data=data, actual_time=time, array=data_currency, name=charcode)

@app.route('/<name>')
def get_data(name):
    data = get_currency(database, name)

    cur = [key['Value'] for key in data]

    currency = {name: cur}

    print(jsonify(cur))

    return jsonify(cur)

@app.route('/<currency>')
def redirect_to_currency_page(currency):

    if database == 'mongodb':

        data = get_currency(database, currency)
        data = sorted(data, key=lambda x: x['Date'], reverse=True)
        data_graph = list()
        for key in data:
            val = list()
            date = datetime.datetime.strptime(key['Date'], "%d.%m.%Y")
            val.append(int(time.mktime(date.timetuple()) * 1000 + 10800000))
            val.append(key['Value'])
            data_graph.append(val)

    elif database == 'postgres':

        value = get_currency(database, currency)
        data = list()
        for i in value:
            valute = dict()
            valute['Date'] = i[0]
            valute['Name'] = i[1]
            valute['CharCode'] = i[2]
            valute['Value'] = i[3]
            data.append(valute)
        data = sorted(data, key=lambda x: x['Date'], reverse=True)

    return render_template('currency.html', currency_list=data, name=currency, array=data_graph)


app.run(port=8086)
