from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers import *
from datetime import datetime, timedelta
import requests

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
        token_creation_time = datetime.now()
        refresh_token = str(token)
        access_token = str(token.access_token)

        res = Response(
            {
                "user": serializer.data,
                "message": "로그인에 성공했습니다",
                "token": {
                    "access": access_token,
                    "refresh": refresh_token,
                    "expiration_time": token_creation_time + timedelta(minutes=5)
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