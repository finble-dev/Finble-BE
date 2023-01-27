from django.shortcuts import get_object_or_404
from .serializers import *
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter

def calculate_profit(portfolio):
    stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
    exchange_rate = 1
    if stock.market == 'US':
        exchange_rate = ExchangeRate.objects.all().order_by('-date')[0].rate  # 현재 환율
    present_val = Price.objects.filter(symbol=portfolio.symbol).order_by('-date')[
                      0].close * exchange_rate * portfolio.quantity  # 현재 가치
    invested_val = portfolio.average_price * portfolio.quantity * exchange_rate  # 투자 금액
    gain = present_val - invested_val  # 평가 손익
    profit_rate = gain / invested_val * 100  # 수익률
    return present_val, invested_val, gain, profit_rate


def sort_ratio(category, ratio_list):
    sorted_list = sorted(ratio_list, key=itemgetter('ratio'), reverse=True)
    if len(sorted_list) > 8:
        sorted_list[7][category] = "기타"
        for i in range(8, len(sorted_list)):
            sorted_list[7]['ratio'] += sorted_list[i]['ratio']
        return sorted_list[0:8]
    else:
        return sorted_list


class Backtest:
    def get_exchange_rate(self, date):
        return ExchangeRate.objects.filter(date__gte=date).exclude(rate=None).order_by('-date')[0].rate

    def get_price(self, symbol, date):
        try:
            return Price.objects.filter(symbol=symbol, date__lte=date).order_by('-date')[0].close
        except:
            return -1

    def get_date_val(self, portfolio, date):
        stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
        # backtest_quantity = self.get_backtest_quantity(portfolio=portfolio)
        exchange_rate = 1
        exchange_rate_past = 1
        if stock.market == 'US':
            exchange_rate = self.get_exchange_rate(date=date)  # 당시 환율
            exchange_rate_past = self.get_exchange_rate(date=datetime.now() - relativedelta(years=1))  # 1년전 환율
        present_val = self.get_price(symbol=portfolio.symbol, date=datetime.now()) * exchange_rate * portfolio.quantity  # 현재 가치
        past_price = self.get_price(symbol=portfolio.symbol, date=datetime.now()-relativedelta(years=1)) * exchange_rate_past  # 1년 전 주가
        backtest_quantity = present_val / past_price
        date_val = self.get_price(symbol=portfolio.symbol, date=date) * exchange_rate * backtest_quantity
        return date_val

    def get_date_val_test(self, portfolio, date, rebalance_quantity):
        stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
        past_date = datetime.now().date() - relativedelta(years=10)
        exchange_rate = 1
        if stock.market == 'US':
            exchange_rate = self.get_exchange_rate(date=date)  # 당시 환율
        date_val = self.get_price(symbol=portfolio.symbol, date=date) * exchange_rate * rebalance_quantity[portfolio.symbol_id]
        return date_val

    def calculate_ratio(self, portfolio_objects, date):
        ratio_list = {'total': 0}

        for portfolio in portfolio_objects:
            if self.get_price(portfolio.symbol_id, date) == -1:
                ratio_list[portfolio.symbol_id] = 0
            else:
                ratio_list[portfolio.symbol_id] = portfolio.ratio
                ratio_list['total'] += portfolio.ratio

        if ratio_list['total'] == 0:
            return ratio_list
        else:
            ratio_list = {key: (value/ratio_list['total']) for key, value in ratio_list.items() if key != 'total'}
        print(ratio_list)
        return ratio_list

    def calculate_quantity(self, test_portfolio, date, val_sum):
        quantity_list = {}
        exchange_rate = 1
        ratio_list = self.calculate_ratio(test_portfolio, date)

        for portfolio in test_portfolio:
            stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
            if stock.market == 'US':
                exchange_rate = self.get_exchange_rate(date=date)  # 당시 환율
            quantity_list[portfolio.symbol_id] = (val_sum * ratio_list[portfolio.symbol_id]) / (self.get_price(portfolio.symbol_id, date) * exchange_rate)

        return quantity_list

    def calculate_annual_average_profit(self, graph):
        profit_result = []
        first_data = graph[0]['data']
        first_date = graph[0]['date']

        for i in range(9, -1, -1):
            d = next(item for item in graph if item['date'] >= graph[-1]['date'] - relativedelta(years=i))
            last_data = d['data']

            profit_result.append(
                {
                    'first_date': first_date,
                    'last_date': d['date'],
                    'profit': (last_data - first_data) / first_data * 100
                }
            )

            if i != 0:
                first_data = graph[graph.index(d) + 1]['data']
                first_date = graph[graph.index(d) + 1]['date']

        return profit_result