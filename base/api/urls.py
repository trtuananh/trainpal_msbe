from django.urls import path
from . import views

urlpatterns = [
    path('',  views.getRoutes),
    path('login/', views.loginUser, name="login"),
    # path('logout/', views.logoutUser, name="logout"),
    # path('register/', views.registerPage, name="register"),

    # path('rooms/', views.getRooms),
    # path('rooms/<str:pk>/', views.getRoom),
]
