from rest_framework_simplejwt.views import TokenRefreshView
from .views import *
from django.urls import path

urlpatterns = [
    path('login/', GoogleLoginView.as_view()),
    path('login/refresh/', TokenRefreshView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('portfolio/', PortfolioView.as_view()),
    path('portfolio/analysis', PortfolioAnalysisView.as_view()),
    path('test-portfolio/', TestPortfolioView.as_view()),
    path('test-portfolio/analysis/', TestPortfolioAnalysisView.as_view()),
    path('search/', StockView.as_view())
]
