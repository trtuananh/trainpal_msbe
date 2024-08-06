from django.urls import path
from . import views

urlpatterns = [
    path('',  views.getRoutes),
    path('login/', views.loginUser, name="api-login"),
    path('logout/', views.logoutUser, name="api-logout"),
    path('register/', views.registerUser, name="api-register"),

    path('profile/<str:pk>/', views.userProfile, name="api-user-profile"),
    path('update-profile/', views.updateProfile, name="api-update-user"),

    path('sport/', views.getLocations, name="api-location"),

    path('location/', views.getLocations, name="api-location"),
    path('add-location/', views.addLocation, name="api-add-location"),
    path('delete-location/<str:pk>/', views.deleteLocation, name="api-delete-location"),

    path('payment/', views.getPaymentMethods, name="api-payment"),
    path('add-payment/', views.addPaymentMethods, name="api-add-payment"),
    path('delete-payment/<str:pk>/', views.deletePaymentMethod, name="api-delete-payment"),
    path('make-payment/', views.makePayment, name="api-make-payment"),
    path('payment-history/', views.getPaymentHistory, name="api-payment-history"),

    path('chatroom/', views.getChatRooms, name="api-chatroom"),
    path('chatroom/<str:pk>/', views.getMessages, name="api-message"),
    path('create-chatroom/', views.createChatRoom, name="api-create-chatroom"),
    path('send-message/', views.sendMessage, name="api-send-message"),

    path('course/', views.getCourses, name="api-courses"),
    path('course/<str:pk>/', views.getCourse, name="api-course"),
    path('create-course/', views.createCourse, name="api-create-course"),
    path('update-course/', views.updateCourse, name="api-update-course"),
    path('delete-course/<str:pk>/', views.deleteCourse, name="api-delete-course"),

    path('training/', views.getTrainingSessions, name="api-training-sessions"),
    path('training/<str:pk>/', views.getTrainingSession, name="api-training-session"),
    path('add-training/', views.addTrainingSession, name="api-add-training-session"),
    path('delete-training/<str:pk>/', views.deleteTrainingSession, name="api-add-training-session"),

    # path('rooms/', views.getRooms),
    # path('rooms/<str:pk>/', views.getRoom),
]
