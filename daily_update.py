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

def update_kr_data_to_db_daily():
    print('hello')
    stock_list = Stock.objects.filter(market='KR')
    now = datetime.now()

    for stock in stock_list:
        try:
            datas = fdr.DataReader(stock.symbol, now.date())['Close']
        except:
            print(f'Got An Error on Symbol:{stock.symbol:8}')
            continue

        Price.objects.create(
            symbol=Stock.objects.get(symbol=stock.symbol),
            date=now.date(),
            close=datas[now.date()]
        )

    print(f'======FINISH update Price table: running time {datetime.now() - now} secs======')


def update_us_data_to_db_daily():
    stock_list = Stock.objects.filter(market='US')
    now = datetime.now()

    for stock in stock_list:
        try:
            datas = fdr.DataReader(stock.symbol, now.date())['Close']
        except:
            print(f'Got An Error on Symbol:{stock.symbol:8}')
            continue

        Price.objects.create(
            symbol=Stock.objects.get(symbol=stock.symbol),
            date=now.date(),
            close=datas[now.date()]
        )

    print(f'======FINISH update Price table: running time {datetime.now() - now} secs======')