from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.utils import json
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from multiprocessing import Pool
from operator import itemgetter
import requests


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
        return ExchangeRate.objects.filter(date__lte=date).exclude(rate=None).order_by('-date')[0].rate

    def get_price(self, symbol, date):
        return Price.objects.filter(symbol=symbol, date__lte=date).order_by('-date')[0].close

    # def get_backtest_quantity(self, portfolio):
    #     stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
    #     exchange_rate = 1
    #     exchange_rate_past = 1
    #     if stock.market == 'US':
    #         exchange_rate = self.get_exchange_rate(date=datetime.now())  # 현재 환율
    #         exchange_rate_past = self.get_exchange_rate(date=datetime.now()-relativedelta(years=1))  # 1년전 환율
    #     present_val = self.get_price(symbol=portfolio.symbol, date=datetime.now()) * exchange_rate * portfolio.quantity  # 현재 가치
    #     past_price = self.get_price(symbol=portfolio.symbol, date=datetime.now()-relativedelta(years=1)) * exchange_rate_past  # 1년 전 주가
    #     backtest_quantity = present_val / past_price
    #     return backtest_quantity

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

    def get_date_val_test(self, portfolio, date, present_val_sum):
        stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
        stock_invested_val = portfolio.ratio * present_val_sum / 100
        past_date = datetime.now().date() - relativedelta(years=10)
        past_price = self.get_price(stock.symbol, past_date)
        quantity = stock_invested_val / past_price
        exchange_rate = 1
        if stock.market == 'US':
            exchange_rate = self.get_exchange_rate(date=date)  # 당시 환율
        date_val = self.get_price(symbol=portfolio.symbol, date=date) * exchange_rate * quantity
        return date_val

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


class GoogleLoginView(APIView):
    def post(self, request):
        payload = {'access_token': request.data.get('token')}  # validate the token
        r = requests.get('https://www.googleapis.com/oauth2/v1/userinfo', params=payload)
        jsondata = r.json()

        if 'error' in jsondata:
            content = {'message': 'wrong google token / this google token is already expired.'}
            return Response(content)

        try:
            user = User.objects.get(email=jsondata['email'])
            serializer = UserSerializer(instance=user)

        except User.DoesNotExist:
            data = {
                "name": jsondata['name'],
                "first_name": jsondata['given_name'],
                "last_name": jsondata['family_name'],
                "email": jsondata['email'],
                "password": make_password(BaseUserManager().make_random_password())  # provide random default password
            }
            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                user = serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token = TokenObtainPairSerializer.get_token(user)
        refresh_token = str(token)
        access_token = str(token.access_token)

        res = Response(
            {
                "user": serializer.data,
                "message": "로그인에 성공했습니다",
                "token": {
                    "access": access_token,
                    "refresh": refresh_token,
                },
            },
            status=status.HTTP_200_OK,
        )
        res.set_cookie("access", access_token, httponly=True)
        res.set_cookie("refresh", refresh_token, httponly=True)
        return res


class LogoutView(APIView):
    def post(self, request):
        response = Response({
            "message": "Logout success"
            }, status=status.HTTP_202_ACCEPTED)
        response.delete_cookie('access')
        response.delete_cookie('refresh')
        return response


class PortfolioView(APIView):
    def get(self, request):
        portfolios = Portfolio.objects.filter(user=request.user.id)
        serializer = PortfolioSerializer(portfolios, many=True)
        response = {
            'status': status.HTTP_200_OK,
            'data': []
        }
        for i in range(portfolios.count()):
            stock = get_object_or_404(Stock, symbol=portfolios[i].symbol_id)
            response['data'].append(
                {
                    'portfolio': serializer.data[i],
                    'stock_detail': StockSerializer(stock).data,
                    'present_val': calculate_profit(portfolios[i])[0],
                    'gain': calculate_profit(portfolios[i])[2],
                    'profit_rate': calculate_profit(portfolios[i])[3]
                }
            )
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

        for kospi in kospi_year:
            date = kospi.date
            graph_kospi.append(
                {
                    'date': date,
                    'data': present_val_sum * kospi.index / kospi_year_ago
                }
            )
            portfolio_val_sum = 0
            for portfolio in portfolio_objects:
                portfolio_val_sum += backtest.get_date_val(portfolio=portfolio, date=date)
            graph_portfolio.append(
                {
                    'date': date,
                    'data': portfolio_val_sum
                }
            )

        kospi_profit = (graph_kospi[-1]['data'] - graph_kospi[0]['data']) / graph_kospi[0]['data'] * 100
        kospi_max_loss = max(d['data'] for d in graph_kospi) - min(d['data'] for d in graph_kospi)
        kospi_max_fall = kospi_max_loss / max(d['data'] for d in graph_kospi) * 100
        portfolio_profit = (graph_portfolio[-1]['data'] - graph_portfolio[0]['data']) / graph_portfolio[0]['data'] * 100
        portfolio_max_loss = max(d['data'] for d in graph_portfolio) - min(d['data'] for d in graph_portfolio)
        portfolio_max_fall = portfolio_max_loss / max(d['data'] for d in graph_portfolio) * 100

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
        present_val_sum = 0
        backtest = Backtest()

        for test_portfolio in test_portfolio_objects:
            if test_portfolio.ratio is None:
                response = Response({
                    "message": "test portfolio's ratio is None"
                }, status=status.HTTP_405_METHOD_NOT_ALLOWED)
                return response

        for portfolio in original_portfolio_objects:
            present_val_sum += calculate_profit(portfolio)[0]

        graph_original_portfolio = []
        graph_test_portfolio = []

        for example in Price.objects.filter(symbol=test_portfolio_objects[0].symbol, date__gte=datetime.now().date()-relativedelta(years=10)):
            original_portfolio_val_sum = 0
            test_portfolio_val_sum = 0

            for original_portfolio in original_portfolio_objects:
                original_portfolio_val_sum += backtest.get_date_val(portfolio=original_portfolio, date=example.date)

            graph_original_portfolio.append(
                {
                    'date': example.date,
                    'data': original_portfolio_val_sum
                }
            )

            for test_portfolio in test_portfolio_objects:
                test_portfolio_val_sum += backtest.get_date_val_test(portfolio=test_portfolio, date=example.date, present_val_sum=float(present_val_sum))

            graph_test_portfolio.append(
                {
                    'date': example.date,
                    'data': test_portfolio_val_sum
                }
            )

        annual_profit_original = backtest.calculate_annual_average_profit(graph_original_portfolio)
        annual_profit_test = backtest.calculate_annual_average_profit(graph_test_portfolio)

        original_portfolio_profit = (graph_original_portfolio[-1]['data'] - graph_original_portfolio[0]['data']) / graph_original_portfolio[0]['data'] * 100
        original_portfolio_max_loss = max(d['data'] for d in graph_original_portfolio) - min(d['data'] for d in graph_original_portfolio)
        original_portfolio_max_fall = original_portfolio_max_loss / max(d['data'] for d in graph_original_portfolio) * 100

        test_portfolio_profit = (graph_test_portfolio[-1]['data'] - graph_test_portfolio[0]['data']) / graph_test_portfolio[0]['data'] * 100
        test_portfolio_max_loss = max(d['data'] for d in graph_test_portfolio) - min(d['data'] for d in graph_test_portfolio)
        test_portfolio_max_fall = test_portfolio_max_loss / max(d['data'] for d in graph_test_portfolio) * 100

        response = {
            'status': status.HTTP_200_OK,
            'data': {
                'present_val_sum': present_val_sum,
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


class StockView(APIView):
    serializer_class = StockSerializer

    def post(self, request):
        search = request.data.get("search")

        if search is None:
            return Response(status=400)

        stock_list = Stock.objects.filter(Q(symbol__icontains=search) | Q(name__icontains=search)).distinct()
        serializer = StockSerializer(stock_list, many=True)
        return Response(serializer.data)


class ContactView(APIView):
    def post(self, request):
        data = {
            "contact": request.data.get("contact"),
            "user": request.user.id
        }

        serializer = ContactSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)