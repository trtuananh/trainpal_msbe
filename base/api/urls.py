from django.urls import path
from . import views

urlpatterns = [
    path('',  views.getRoutes),
    path('login/', views.loginUser, name="api-login"),
    path('logout/', views.logoutUser, name="api-logout"),
    path('register/', views.registerUser, name="api-register"),
    path('token-refresh/', views.TokenRefreshView.as_view(), name='token_refresh'),

    path('profile/<str:pk>/', views.userProfile, name="api-user-profile"),
    path('update-profile/', views.updateProfile, name="api-update-user"),

    path('sport/', views.getLocations, name="api-location"),

    path('location/', views.getLocations, name="api-location"),
    path('add-location/', views.addLocation, name="api-add-location"),
    path('delete-location/<str:pk>/', views.deleteLocation, name="api-delete-location"),

    path('payment/', views.getPayments, name="api-payments"),
    path('payment/<str:pk>/', views.getPayment, name="api-payment"),
    path('create-payment/', views.createPayment, name="api-create-payment"),
    path('momo-payment/', views.momoPayment, name="api-momo-payment"),
    path('momo-payment-callback/', views.momoPaymentCallback, name="api-momo-payment-callback"),
    path('verify-payment/', views.verifyMomoPayment, name="api-verify-payment"),

    path('chatroom/', views.getChatRoom, name="api-chatroom"),
    path('create-chatroom/', views.createChatRoom, name="api-create-chatroom"),
    path('message/', views.getMessages, name="api-message"),
    path('last-seen/', views.lastSeen, name="api-last-seen"),

    path('course/', views.getCourses, name="api-courses"),
    path('course/<str:pk>/', views.getCourse, name="api-course"),
    path('course/<str:course_pk>/rating', views.getRatings, name="api-ratings"),
    path('create-course/', views.createCourse, name="api-create-course"),
    path('update-course/', views.updateCourse, name="api-update-course"),
    path('delete-course/<str:pk>/', views.deleteCourse, name="api-delete-course"),

    path('training/', views.getTrainingSessions, name="api-training-sessions"),
    path('training/<str:pk>/', views.getTrainingSession, name="api-training-session"),
    path('add-training/', views.addTrainingSession, name="api-add-training-session"),
    path('delete-training/<str:pk>/', views.deleteTrainingSession, name="api-add-training-session"),

    path('booking/', views.getBookingSessions, name="api-booking-sessions"),
    path('booking/<str:pk>/', views.getBookingSession, name="api-booking-session"),
    path('add-booking/', views.addBookingSession, name="api-add-booking-session"),
    path('delete-booking/<str:pk>/', views.deleteBookingSession, name="api-add-booking-session"),

    path('add-rating/', views.addRating, name="api-add-rating"),
]
