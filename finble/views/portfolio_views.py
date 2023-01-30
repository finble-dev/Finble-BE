from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from ..functions import *
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from multiprocessing import Pool
from operator import itemgetter
import requests


class PortfolioView(APIView):
    def get(self, request):
        portfolios = Portfolio.objects.filter(user=request.user.id)
        serializer = PortfolioSerializer(portfolios, many=True)
        total_gain = 0
        total_invested = 0

        data = []

        for i in range(portfolios.count()):
            stock = get_object_or_404(Stock, symbol=portfolios[i].symbol_id)
            total_gain += calculate_profit(portfolios[i])[2]
            total_invested += calculate_profit(portfolios[i])[1]
            data.append(
                {
                    'portfolio': serializer.data[i],
                    'stock_detail': StockSerializer(stock).data,
                    'present_val': calculate_profit(portfolios[i])[0],
                    'gain': calculate_profit(portfolios[i])[2],
                    'profit_rate': calculate_profit(portfolios[i])[3]
                }
            )
        response = {
            'status': status.HTTP_200_OK,
            'data': data,
            'total_gain': total_gain,
            'total_profit_rate': total_gain / total_invested * 100
        }

        return Response(response)

    def post(self, request):

        portfolio = Portfolio.objects.filter(user=request.user.id, symbol=request.data.get("symbol")).first()

        if portfolio is None:
            data1 = {
                "symbol": request.data.get("symbol"),
                "user": request.user.id,
                "average_price": request.data.get("average_price"),
                "quantity": request.data.get("quantity")
            }
            data2 = {
                "symbol": request.data.get("symbol"),
                "user": request.user.id,
                "is_from_portfolio": True
            }
            serializer1 = PortfolioSerializer(data=data1)
            serializer2 = TestPortfolioSerializer(data=data2)
            if serializer1.is_valid():
                if serializer2.is_valid():
                    serializer1.save()
                    serializer2.save()
                    response = {
                        'status': status.HTTP_200_OK,
                        'data': {
                            'portfolio': serializer1.data,
                            'test_portfolio': serializer2.data
                        }
                    }
                    return Response(response)
                return Response(serializer2.errors, status=400)
            return Response(serializer1.errors, status=400)

        else:
            new_quantity = portfolio.quantity + request.data.get("quantity")
            new_average_price = (portfolio.average_price * portfolio.quantity + request.data.get(
                "average_price") * request.data.get("quantity")) / new_quantity
            data = {
                "symbol": request.data.get("symbol"),
                "user": request.user.id,
                "average_price": new_average_price,
                "quantity": new_quantity
            }
            serializer = PortfolioSerializer(instance=portfolio, data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=200)
            else:
                return Response(serializer.errors, status=400)

    # def patch(self, request):
    #     portfolio_instance = get_object_or_404(Portfolio, id=request.data['id'])
    #     serializer = PortfolioSerializer(instance=portfolio_instance, data=request.data, partial=True)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=201)
    #     return Response(serializer.errors, status=400)

    def delete(self, request):
        portfolio = Portfolio.objects.filter(id=request.data['id'])
        test_portfolio = TestPortfolio.objects.filter(user=request.user.id, symbol=portfolio[0].symbol)
        portfolio.delete()
        test_portfolio.delete()
        return Response({"delete success"}, status=204)


class PortfolioAnalysisView(APIView):
    def get(self, request):
        portfolio_objects = Portfolio.objects.filter(user=request.user.id)
        present_val_sum = 0
        invested_val_sum = 0
        for portfolio in portfolio_objects:
            present_val_sum += calculate_profit(portfolio)[0]
            invested_val_sum += calculate_profit(portfolio)[1]

        portfolio_ratio = []
        sector_ratio = []

        for portfolio in portfolio_objects:
            stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
            ratio = calculate_profit(portfolio)[0] / present_val_sum * 100
            portfolio_ratio.append(
                {
                    'stock': StockSerializer(stock).data,
                    'ratio': ratio
                }
            )
            if stock.sector in (d['sector'] for d in sector_ratio):
                d = next(item for item in sector_ratio if item['sector'] == stock.sector)
                d['ratio'] += ratio
            else:
                sector_ratio.append(
                    {
                        'sector': stock.sector,
                        'ratio': ratio
                    }
                )

        portfolio_ratio = sort_ratio("stock", portfolio_ratio)
        sector_ratio = sorted(sector_ratio, key=itemgetter('ratio'), reverse=True)

        kospi_year = Kospi.objects.filter(date__gte=datetime.now()-relativedelta(years=1))
        kospi_year_ago = kospi_year[0].index
        graph_kospi = []
        graph_portfolio = []
        backtest = Backtest()

        i = 0
        k = int(kospi_year.count() / 40)
        for kospi in kospi_year:
            i += 1
            if i % k != 1:
                continue
            graph_kospi.append(
                {
                    'date': kospi.date,
                    'data': present_val_sum * kospi.index / kospi_year_ago
                }
            )
            portfolio_val_sum = 0
            for portfolio in portfolio_objects:
                portfolio_val_sum += backtest.get_date_val(portfolio=portfolio, date=kospi.date)
            graph_portfolio.append(
                {
                    'date': kospi.date,
                    'data': portfolio_val_sum
                }
            )

        kospi_profit = (graph_kospi[-1]['data'] - graph_kospi[0]['data']) / graph_kospi[0]['data'] * 100

        kospi_max_loss = calculate_max_fall(graph_kospi)[0]
        kospi_max_fall = calculate_max_fall(graph_kospi)[1]
        portfolio_profit = (graph_portfolio[-1]['data'] - graph_portfolio[0]['data']) / graph_portfolio[0]['data'] * 100
        portfolio_max_loss = calculate_max_fall(graph_portfolio)[0]
        portfolio_max_fall = calculate_max_fall(graph_portfolio)[1]

        response = {
            'status': status.HTTP_200_OK,
            'data': {
                'present_val_sum': present_val_sum,
                'invested_val_sum': invested_val_sum,
                'portfolio_ratio': portfolio_ratio,
                'sector_ratio': sector_ratio,
                'graph_kospi': graph_kospi,
                'graph_portfolio': graph_portfolio,
                'kospi_profit': kospi_profit,
                'kospi_max_fall': kospi_max_fall,
                'kospi_max_loss': kospi_max_loss,
                'portfolio_profit': portfolio_profit,
                'portfolio_max_fall': portfolio_max_fall,
                'portfolio_max_loss': portfolio_max_loss
            }
        }
        return Response(response)