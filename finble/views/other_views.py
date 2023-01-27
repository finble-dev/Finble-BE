from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from ..serializers import *
from ..functions import *


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