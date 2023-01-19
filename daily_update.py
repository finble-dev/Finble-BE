import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finble_backend.settings')
django.setup()

import FinanceDataReader as fdr
from datetime import datetime
from dateutil.relativedelta import relativedelta
from finble.models import *


def update_kr_data_to_db_daily():
    stock_list = Stock.objects.filter(market='KR')
    now = datetime.now()
    count = 0

    for stock in stock_list:
        try:
            datas = fdr.DataReader(stock.symbol, now.date())['Close']
        except:
            print(f'Got An Error on Symbol:{stock.symbol:8}')
            continue

        Price.objects.create(
            symbol=Stock.objects.get(symbol=stock.symbol),
            date=datas.index[0],
            close=datas[datas.index[0]]
        )
        count += 1

    print(f'====== Day: {now} FINISH update KR Price table {count} datas ======')


def update_us_data_to_db_daily():
    stock_list = Stock.objects.filter(market='US')
    today = datetime.now().date() - relativedelta(days=1)
    count = 0

    for stock in stock_list:
        try:
            datas = fdr.DataReader(stock.symbol, today)['Close']
        except:
            print(f'Got An Error on Symbol:{stock.symbol:8}')
            continue

        Price.objects.create(
            symbol=Stock.objects.get(symbol=stock.symbol),
            date=datas.index[0],
            close=datas[datas.index[0]]
        )
        count += 1

    print(f'====== Day: {today} FINISH update US Price table {count} datas ======')
