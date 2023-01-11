from .views import *
from django.urls import path

urlpatterns = [
    path('login/', GoogleLoginView.as_view()),
    path('portfolio/', PortfolioView.as_view()),
]
