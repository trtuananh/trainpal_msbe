from django.urls import path
from . import views

app_name = 'user_service'

urlpatterns = [
    path('login/', views.login_user, name="login"),
    path('logout/', views.logout_user, name="logout"),
    path('register/', views.register_user, name="register"),
    path('token-refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/<str:pk>/', views.user_profile, name="user_profile"),
    path('update-profile/', views.update_profile, name="update_profile"),
]
