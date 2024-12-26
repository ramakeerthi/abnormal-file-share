from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, LoginView, LogoutView, TOTPSetupView, CheckAuthView, CookieTokenRefreshView, UserManagementView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('mfa/setup/', TOTPSetupView.as_view(), name='mfa-setup'),
    path('check-auth/', CheckAuthView.as_view(), name='check-auth'),
    path('users/', UserManagementView.as_view(), name='user-management'),
]