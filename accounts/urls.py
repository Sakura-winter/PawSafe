from django.urls import path
from .views import RegisterView, LoginView, register_page, login_page, dashboard_page, user_page
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register-page/', register_page),
    path('dashboard/', dashboard_page, name='dashboard'),
    path('user/', user_page, name='user_page'),
    path('login-page/', login_page),
]