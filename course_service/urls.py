from django.urls import path
from . import views

app_name = 'course_service'

urlpatterns = [
    path('courses/', views.get_courses, name="courses"),
    path('course/<str:pk>/', views.get_course, name="course"),
    path('course/<str:course_pk>/rating/', views.get_ratings, name="ratings"),
    path('create-course/', views.create_course, name="create_course"),
    path('update-course/', views.update_course, name="update_course"),
    path('delete-course/<str:pk>/', views.delete_course, name="delete_course"),
    path('training/', views.get_training_sessions, name="training_sessions"),
    path('training/<str:pk>/', views.get_training_session, name="training_session"),
    path('add-training/', views.add_training_session, name="add_training_session"),
    path('delete-training/<str:pk>/', views.delete_training_session, name="delete_training_session"),
    path('booking/', views.get_booking_sessions, name="booking_sessions"),
    path('booking/<str:pk>/', views.get_booking_session, name="booking_session"),
    path('add-booking/', views.add_booking_session, name="add_booking_session"),
    path('delete-booking/<str:pk>/', views.delete_booking_session, name="delete_booking_session"),
    path('add-rating/', views.add_rating, name="add_rating"),
]
