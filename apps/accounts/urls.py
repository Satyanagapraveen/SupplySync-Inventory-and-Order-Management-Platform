from .views import RegisterView,LoginView
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

urlspatterns=[
    path('register/',RegisterView.as_view(),name='register'),
    path('/login',LoginView.as_view(),name='login'),
    path('/token/refresh',TokenRefreshView.as_view(),name='token_refresh'),
]