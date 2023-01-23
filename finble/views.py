from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework.utils import json
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

# Create your views here.

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

class Backtest:
    def get_exchange_rate(self, date):
        return ExchangeRate.objects.filter(date__lte=date).order_by('-date')[0].rate

    def get_price(self, symbol, date):
        return Price.objects.filter(symbol=symbol, date__lte=date).order_by('-date')[0].close

    def get_backtest_quantity(self, portfolio):
        stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
        exchange_rate = 1
        exchange_rate_past = 1
        if stock.market == 'US':
            exchange_rate = self.get_exchange_rate(date=datetime.now())  # 현재 환율
            exchange_rate_past = self.get_exchange_rate(date=datetime.now()-relativedelta(years=1))  # 1년전 환율
        present_val = self.get_price(symbol=portfolio.symbol, date=datetime.now()) * exchange_rate * portfolio.quantity  # 현재 가치
        past_price = self.get_price(symbol=portfolio.symbol, date=datetime.now()-relativedelta(years=1)) * exchange_rate_past  # 1년 전 주가
        backtest_quantity = present_val / past_price
        return backtest_quantity

    def get_date_val(self, portfolio, date):
        stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
        backtest_quantity = self.get_backtest_quantity(portfolio=portfolio)
        exchange_rate = 1
        if stock.market == 'US':
            exchange_rate = self.get_exchange_rate(date=date)  # 당시 환율
        date_val = self.get_price(symbol=portfolio.symbol, date=date) * exchange_rate * backtest_quantity
        return date_val

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
                "username": jsondata['name'],
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

        kospi_year = Kospi.objects.filter(date__gte=datetime.now()-relativedelta(years=1))
        graph_kospi = []
        graph_portfolio = []
        for kospi in kospi_year:
            graph_kospi.append(
                {
                    'date': kospi.date,
                    'data': present_val_sum * kospi.index / kospi_year[0].index
                }
            )
            portfolio_val_sum = 0
            for portfolio in portfolio_objects:
                backtest = Backtest()
                portfolio_val_sum += backtest.get_date_val(portfolio=portfolio, date=kospi.date)
            graph_portfolio.append(
                {
                    'date': kospi.date,
                    'data': portfolio_val_sum
                }
            )

        kospi_profit = (graph_kospi[-1]['data'] - graph_kospi[0]['data']) / graph_kospi[0]['data'] * 100
        portfolio_profit = (graph_portfolio[-1]['data'] - graph_portfolio[0]['data']) / graph_portfolio[0]['data'] * 100
        max_loss = max(d['data'] for d in graph_portfolio) - min(d['data'] for d in graph_portfolio)
        max_fall = max_loss / max(d['data'] for d in graph_portfolio) * 100

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
                'portfolio_profit': portfolio_profit,
                'max_fall': max_fall,
                'max_loss': max_loss
            }
        }
        return Response(response)


class TestPortfolioView(APIView):
    def get(self, request):
        test_portfolios = TestPortfolio.objects.filter(user=request.user.id)
        serializer = TestPortfolioSerializer(test_portfolios, many=True)
        response = {
            'status': status.HTTP_200_OK,
            'data': []
        }
        for i in range(test_portfolios.count()):
            stock = get_object_or_404(Stock, symbol=test_portfolios[i].symbol_id)
            response['data'].append(
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


# class TestPortfolioAnalysisView(APIView):
# 백테스트 코드


class StockView(APIView):
    serializer_class = StockSerializer

    def post(self, request):
        search = request.data.get("search")

        if search is None:
            return Response(status=400)

        stock_list = Stock.objects.filter(Q(symbol__icontains=search) | Q(name__icontains=search)).distinct()
        serializer = StockSerializer(stock_list, many=True)
        return Response(serializer.data)

