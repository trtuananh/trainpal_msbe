from django.urls import path
from . import views

urlpatterns = [
    path('',  views.getRoutes),
    path('login/', views.loginUser, name="api-login"),
    path('logout/', views.logoutUser, name="api-logout"),
    path('register/', views.registerUser, name="api-register"),

    path('profile/<str:pk>/', views.userProfile, name="api-user-profile"),
    path('update-profile/', views.updateProfile, name="api-update-user"),

    path('location/', views.getLocations, name="api-location"),
    path('add-location/', views.getLocations, name="api-location"),

    # path('rooms/', views.getRooms),
    # path('rooms/<str:pk>/', views.getRoom),
]
