import os
import django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BASE_DIR.finble_backend.settings')
django.setup()

import FinanceDataReader as fdr
import datetime
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from models import *


def get_price_data():
    stock_list = Stock.objects.all()
    now = datetime.now()
    before = now - relativedelta(years=10)

    check = 0
    for stock in stock_list:
        datas = fdr.DataReader(stock.symbol, before, now)['Close']
        date = datas.index

        for i in date:
            # print(i, "|", datas[i])
            Price.objects.create(
                symbol=Stock.objects.get(symbol=stock.symbol),
                date=i.date(),
                close=datas[i]
            )

        print(f'Symbol:{stock.symbol:8} Market:{stock.market:6} Name:{stock.name:8} Count:{len(datas):4}')

    print(f'FINISH update Price table: running time {datetime.now() - now} secs')


def get_kospi_data():
    now = datetime.now()
    before = now - relativedelta(years=1)
    datas = fdr.DataReader('KS11', before, now)['Close']
    date = datas.index

    for i in date:
        Kospi.objects.create(
            date=i.date(),
            index=datas[i]
        )

    print(f'FINISH update Kospi table: running time {datetime.now() - now} secs & {len(datas)} datas')


def get_exchangerate_data():
    now = datetime.now()
    before = now - relativedelta(years=10)
    datas = fdr.DataReader('USD/KRW', before, now)['Close']
    date = datas.index

    print(datas)

    for i in date:
        ExchangeRate.objects.create(
            date=i.date(),
            rate=datas[i]
        )

    print(f'FINISH update Exchange Rate table: running time {datetime.now() - now} secs & {len(datas)} datas')


get_price_data()
get_kospi_data()
get_exchangerate_data()
