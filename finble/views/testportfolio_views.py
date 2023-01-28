from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..functions import *
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class TestPortfolioView(APIView):
    def get(self, request):
        test_portfolios = TestPortfolio.objects.filter(user=request.user.id)
        serializer = TestPortfolioSerializer(test_portfolios, many=True)
        response = {
            'status': status.HTTP_200_OK,
            'data_add': [],
            'data_retain': []
        }
        for i in range(test_portfolios.count()):
            if test_portfolios[i].is_from_portfolio:
                stock = get_object_or_404(Stock, symbol=test_portfolios[i].symbol_id)
                response['data_retain'].append(
                    {
                        'portfolio': serializer.data[i],
                        'stock_detail': StockSerializer(stock).data,
                    }
                )
            else:
                stock = get_object_or_404(Stock, symbol=test_portfolios[i].symbol_id)
                response['data_add'].append(
                    {
                        'portfolio': serializer.data[i],
                        'stock_detail': StockSerializer(stock).data,
                    }
                )
        return Response(response)

    def post(self, request):
        data = {
            "symbol": request.data.get("symbol"),
            "user": request.user.id,
            "is_from_portfolio": False
        }
        serializer = TestPortfolioSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        test_portfolio_instance = get_object_or_404(TestPortfolio, id=request.data['id'])
        serializer = TestPortfolioSerializer(instance=test_portfolio_instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        test_portfolio = TestPortfolio.objects.filter(id=request.data['id'])
        try:
            if test_portfolio[0].is_from_portfolio:
                return Response({"포트폴리오에 있는 주식은 삭제할 수 없습니다"}, status=400)
        except IndexError:
            return Response({"존재하지 않는 test portfolio id"}, status=400)
        test_portfolio.delete()
        return Response({"delete success"}, status=204)


class TestPortfolioAnalysisView(APIView):
    def get(self, request):
        test_portfolio_objects = TestPortfolio.objects.filter(user=request.user.id)
        original_portfolio_objects = Portfolio.objects.filter(user=request.user.id)
        invest_val_sum = 0
        present_val_sum = 0
        not_listed_stocks = []
        original_ratio = {}
        backtest = Backtest()

        for test_portfolio in test_portfolio_objects:
            if test_portfolio.ratio is None:
                response = Response({
                    "message": "test portfolio's ratio is None"
                }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
                return response

        for portfolio in original_portfolio_objects:
            invest_val_sum += calculate_profit(portfolio)[1]
            present_val_sum += calculate_profit(portfolio)[0]
            original_ratio[portfolio.symbol_id] = calculate_profit(portfolio)[0]
            past_price = backtest.get_price(portfolio.symbol_id, datetime.now().date()-relativedelta(years=10))
            if past_price == -1:
                not_listed_stocks.append(Price.objects.filter(symbol=portfolio.symbol_id)[0].date)

        original_ratio = {key: (value / present_val_sum) for key, value in original_ratio.items()}
        original_quantity = backtest.calculate_quantity_original(original_portfolio_objects, original_ratio, present_val_sum, datetime.now().date()-relativedelta(years=10))
        graph_original_portfolio = []
        graph_test_portfolio = []

        rebalance_month = 19
        rebalance_quantity = backtest.calculate_quantity(test_portfolio_objects, datetime.now().date()-relativedelta(years=10), present_val_sum)

        example_list = Price.objects.filter(symbol='AAPL', date__gte=datetime.now().date()-relativedelta(years=10))
        temp = example_list[0].date.month
        temp_slice = 0

        for example in example_list:
            if example.date.month == temp:
                continue
            temp = example.date.month
            original_portfolio_val_sum = 0
            test_portfolio_val_sum = 0


            for original_portfolio in original_portfolio_objects:
                original_portfolio_val_sum += original_quantity[original_portfolio.symbol_id] * backtest.get_price(original_portfolio.symbol_id, example.date)

            if original_portfolio_val_sum > 0:
                graph_original_portfolio.append(
                    {
                        'date': example.date,
                        'data': original_portfolio_val_sum
                    }
                )
            else:
                graph_original_portfolio.append(
                    {
                        'date': example.date,
                        'data': None
                    }
                )
                temp_slice = len(graph_original_portfolio)

            for test_portfolio in test_portfolio_objects:
                test_portfolio_val_sum += backtest.get_date_val_test(portfolio=test_portfolio, date=example.date, rebalance_quantity=rebalance_quantity)

            if test_portfolio_val_sum > 0:
                graph_test_portfolio.append(
                    {
                        'date': example.date,
                        'data': test_portfolio_val_sum
                    }
                )

            for listed_day in not_listed_stocks:
                if example.date >= listed_day:
                    del not_listed_stocks[not_listed_stocks.index(listed_day)]
                    if original_portfolio_val_sum > 0:
                        original_quantity = backtest.calculate_quantity_original(original_portfolio_objects, original_ratio, original_portfolio_val_sum, example.date + relativedelta(days=5))
                    else:
                        original_quantity = backtest.calculate_quantity_original(original_portfolio_objects, original_ratio, present_val_sum, example.date + relativedelta(days=5))

            # rebalancing
            if example.date >= datetime.now().date()-relativedelta(months=rebalance_month*6):
                rebalance_month -= 1
                rebalance_quantity = backtest.calculate_quantity(test_portfolio_objects, example.date, test_portfolio_val_sum)
                # print(example.date, test_portfolio_val_sum, rebalance_quantity)

        temp_original_portfolio = graph_original_portfolio[temp_slice:-1]
        annual_profit_original = ((temp_original_portfolio[-1]['data']/temp_original_portfolio[0]['data']) ** 0.1 - 1) * 100
        annual_profit_test = ((graph_test_portfolio[-1]['data']/graph_test_portfolio[0]['data']) ** 0.1 - 1) * 100

        original_portfolio_profit = (temp_original_portfolio[-1]['data'] - temp_original_portfolio[0]['data']) / temp_original_portfolio[0]['data'] * 100
        original_portfolio_max_loss = max(d['data'] for d in temp_original_portfolio) - min(d['data'] for d in temp_original_portfolio)
        original_portfolio_max_fall = original_portfolio_max_loss / max(d['data'] for d in temp_original_portfolio) * 100

        test_portfolio_profit = (graph_test_portfolio[-1]['data'] - graph_test_portfolio[0]['data']) / graph_test_portfolio[0]['data'] * 100
        test_portfolio_max_loss = max(d['data'] for d in graph_test_portfolio) - min(d['data'] for d in graph_test_portfolio)
        test_portfolio_max_fall = test_portfolio_max_loss / max(d['data'] for d in graph_test_portfolio) * 100

        response = {
            'status': status.HTTP_200_OK,
            'data': {
                'invest_val_sum': invest_val_sum,
                'present_val_sum': graph_original_portfolio[0]['data'],
                'final_val_test': graph_test_portfolio[-1]['data'],
                'annual_profit_original': annual_profit_original,
                'annual_profit_test': annual_profit_test,
                'graph_original_portfolio': graph_original_portfolio,
                'graph_test_portfolio': graph_test_portfolio,
                'original_portfolio_profit': original_portfolio_profit,
                'original_portfolio_max_fall': original_portfolio_max_fall,
                'original_portfolio_max_loss': original_portfolio_max_loss,
                'test_portfolio_profit': test_portfolio_profit,
                'test_portfolio_max_fall': test_portfolio_max_fall,
                'test_portfolio_max_loss': test_portfolio_max_loss
            }
        }
        return Response(response)