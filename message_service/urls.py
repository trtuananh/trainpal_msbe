from django.urls import path
from . import views

app_name = 'message_service'

urlpatterns = [
    path('chatroom/', views.get_chat_room, name="chat_room"),
    path('create-chatroom/', views.create_chat_room, name="create_chat_room"),
    path('messages/<str:room_id>/', views.get_messages, name="messages"),
    path('last-seen/<str:room_id>/', views.last_seen, name="last_seen"),
]
