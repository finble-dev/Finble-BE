from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
class HomeView(APIView):
    def get(self, request):
        return Response({"홈화면(test)"}, status=status.HTTP_200_OK)