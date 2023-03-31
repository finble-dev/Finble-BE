from rest_framework_simplejwt.views import TokenRefreshView
from .views import user_views, portfolio_views, testportfolio_views, other_views
from django.urls import path

urlpatterns = [
    path('login/', user_views.GoogleLoginView.as_view()),
    path('login/refresh/', TokenRefreshView.as_view()),
    path('user-info/', user_views.GetUserInfoView.as_view()),
    path('logout/', user_views.LogoutView.as_view()),
    path('portfolio/', portfolio_views.PortfolioView.as_view()),
    path('portfolio/analysis/', portfolio_views.PortfolioAnalysisView.as_view()),
    path('test-portfolio/', testportfolio_views.TestPortfolioView.as_view()),
    path('test-portfolio/analysis/', testportfolio_views.TestPortfolioAnalysisView.as_view()),
    path('search/', other_views.StockView.as_view()),
    path('contact/', other_views.ContactView.as_view())
]
