import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finble_backend.settings')
django.setup()

import FinanceDataReader as fdr
from datetime import datetime
from dateutil.relativedelta import relativedelta
from finble.models import *
import numpy as np
import asyncio
from asgiref.sync import sync_to_async


@sync_to_async
def get_price_data(num):
    stock_list = Stock.objects.all()
    now = datetime.now()
    start = now.year - num
    end = str(start + 1)

    for stock in stock_list:
        try:
            datas = fdr.DataReader(stock.symbol, str(start), end)['Close']
        except:
            print(f'Got Error on Symbol:{stock.symbol:8} Date:{start} - {end}')
            continue

        date = datas.index

        for i in date:
            Price.objects.create(
                symbol=Stock.objects.get(symbol=stock.symbol),
                date=i.date(),
                close=datas[i]
            )

        print(f'Symbol:{stock.symbol:8} Market:{stock.market:6} Name:{stock.name:8} Count:{len(datas):4}')

    print(f'======FINISH update Price table: running time {datetime.now() - now} secs======')


async def update_price_data_to_db():
    today = datetime.now().year

    coroutines = [get_price_data(i) for i in range(11, 0, -1)]
    await asyncio.gather(*coroutines)


def get_kospi_data():
    now = datetime.now()
    before = now - relativedelta(years=1)
    # datas = fdr.DataReader('KS11', before, now)['Close']
    datas = fdr.DataReader('KS11', '2021')['Close']
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
    datas = fdr.DataReader('USD/KRW', '2022')['Close']
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
# get_exchangerate_data()

asyncio.run(update_price_data_to_db())
