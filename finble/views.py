from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from rest_framework.utils import json
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import *
import requests

# Create your views here.
class GoogleLoginView(APIView):
    def post(self, request):
        payload = {'access_token': request.data.get("token")}  # validate the token
        r = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', params=payload)
        data = json.loads(r.text)

        if 'error' in data:
            content = {'message': 'wrong google token / this google token is already expired.'}
            return Response(content)

        # create user if not exist
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            user = User()
            user.username = data['email']
            # provider random default password
            user.password = make_password(BaseUserManager().make_random_password())
            user.email = data['email']
            user.save()

        token = RefreshToken.for_user(user)  # generate token without username & password
        response = {}
        response['username'] = user.username
        response['access_token'] = str(token.access_token)
        response['refresh_token'] = str(token)
        return Response(response)


class PortfolioView(APIView):

    def get(self, request):
        portfolio = Portfolio.objects.filter(user=request.user.id)
        print(request.user.id)
        serializer = PortfolioSerializer(portfolio, many=True)
        return Response(serializer.data)
    def post(self, request):
        data = {
            "symbol": request.data.get("symbol"),
            "user": request.user.id,
            "average_price": request.data.get("average_price"),
            "quantity": request.data.get("quantity")
        }
        serializer = PortfolioSerializer(data=data)
        print(request.user.id)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(status=status.HTTP_400_BAD_REQUEST)
