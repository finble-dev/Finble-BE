import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finble_backend.settings')
django.setup()

import FinanceDataReader as fdr
import datetime
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from finble.models import *
import numpy as np


def get_price_data():
    stock_list = Stock.objects.all()
    now = datetime.now()
    before = now - relativedelta(years=10)

    for stock in stock_list:
        # datas = fdr.DataReader(stock.symbol, before, now)['Close']
        datas = fdr.DataReader(stock.symbol, '2012')['Close']
        date = datas.index

        for i in date:
            # print(i, "|", datas[i])
            Price.objects.create(
                symbol=Stock.objects.get(symbol=stock.symbol),
                date=i.date(),
                close=datas[i]
            )

        print(f'Symbol:{stock.symbol:8} Market:{stock.market:6} Name:{stock.name:8} Count:{len(datas):4}')

    print(f'FINISH update Price table: running time {datetime.now() - now} secs & {len(datas)} datas')


def get_kospi_data():
    now = datetime.now()
    before = now - relativedelta(years=1)
    # datas = fdr.DataReader('KS11', before, now)['Close']
    datas = fdr.DataReader('KS11', '2022')['Close']
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
    # datas = fdr.DataReader('USD/KRW', before, now)['Close']
    datas = fdr.DataReader('USD/KRW', '2012')['Close']
    datas = datas.replace({np.nan: None})
    date = datas.index

    for i in date:
        try:
            ExchangeRate.objects.create(
                date=i.date(),
                rate=datas[i]
            )
        except:
            print(i.date())
            continue

    print(f'FINISH update Exchange Rate table: running time {datetime.now() - now} secs & {len(datas)} datas')


# get_price_data()
# get_kospi_data()
get_exchangerate_data()
