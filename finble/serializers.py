from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = '__all__'


class TestPortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestPortfolio
        fields = '__all__'
