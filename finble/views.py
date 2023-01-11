from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *

# Create your views here.


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


