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
import requests

# Create your views here.
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

    def calculate_profit(self, portfolio):
        stock = get_object_or_404(Stock, symbol=portfolio.symbol_id)
        exchange_rate = 1
        if stock.market == 'US':
            exchange_rate = ExchangeRate.objects.all().order_by('-date')[0].rate  # 현재 환율
        present_val = Price.objects.filter(symbol=portfolio.symbol).order_by('-date')[0].close * exchange_rate * portfolio.quantity  # 현재 가치
        print(present_val)
        invested_val = portfolio.average_price * portfolio.quantity * exchange_rate  # 투자 금액
        gain = present_val - invested_val  # 평가 손익
        profit_rate = gain/invested_val * 100  # 수익률
        return present_val, gain, profit_rate

    def get(self, request):
        portfolio = Portfolio.objects.filter(user=request.user.id)
        serializer = PortfolioSerializer(portfolio, many=True)
        response = {
            'status': status.HTTP_200_OK,
            'data': []
        }
        for i in range(portfolio.count()):
            response['data'].append(
                {
                    'portfolio': serializer.data[i],
                    'present_val': self.calculate_profit(portfolio=portfolio[i])[0],
                    'gain': self.calculate_profit(portfolio=portfolio[i])[1],
                    'profit_rate': self.calculate_profit(portfolio=portfolio[i])[2]
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


    def patch(self, request):
        portfolio_instance = get_object_or_404(Portfolio, id=request.data['id'])
        serializer = PortfolioSerializer(instance=portfolio_instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def delete(self, request):
        portfolio = Portfolio.objects.filter(id=request.data['id'])
        test_portfolio = TestPortfolio.objects.filter(user=request.user.id, symbol=portfolio[0].symbol)
        portfolio.delete()
        test_portfolio.delete()
        return Response({"delete success"}, status=204)


class PortfolioAnalysisView(APIView):
    def post(self):
        pass  # 내 주식 진단받기 결과


class TestPortfolioView(APIView):
    def get(self, request):
        test_portfolio = TestPortfolio.objects.filter(user=request.user.id)
        serializer = TestPortfolioSerializer(test_portfolio, many=True)
        return Response(serializer.data)

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
    def post(self):
        pass  # 백테스트 코드


class StockView(APIView):
    serializer_class = StockSerializer

    def get(self, request):
        search = request.data.get("search")

        if search is None:
            return Response(status=400)

        stock_list = Stock.objects.filter(Q(symbol__icontains=search) | Q(name__icontains=search)).distinct()
        serializer = StockSerializer(stock_list, many=True)
        return Response(serializer.data)

