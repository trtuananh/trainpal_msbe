import requests
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from . import models
from . import serializers

def check_user_is_trainer(user_id, access_token):
    response = requests.get(
        f"http://localhost:8000/api/user/profile/{user_id}/",
        headers={'Authorization': f'Bearer {access_token}'}
    )
    if response.status_code == 200:
        user_data = response.json()
        return user_data.get('isTrainer', False)
    return False

@api_view(['GET'])
def get_chat_room(request):
    user = request.user
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    is_trainer = check_user_is_trainer(user.id, access_token)
    booking_session_id = request.GET.get('booking_session_id')

    if booking_session_id:
        # Fetch booking session from course_service
        booking_response = requests.get(
            f"http://localhost:8000/api/course/booking/{booking_session_id}/",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if booking_response.status_code != 200:
            return Response({"success": False, "message": "Booking session not found"}, status=400)
        booking_session = booking_response.json()
        course_response = requests.get(
            f"http://localhost:8000/api/course/course/{booking_session['course']['id']}/",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if course_response.status_code != 200:
            return Response({"success": False, "message": "Course not found"}, status=400)
        course = course_response.json()

        chat_room = models.ChatRoom.objects.filter(booking_session_id=booking_session_id).first()
        if not chat_room:
            user_ids = [user.id, course['trainer_id']] if user.id != course['trainer_id'] else [user.id]
            chat_room = models.ChatRoom.objects.create(
                user_ids=user_ids,
                booking_session_id=booking_session_id
            )
            models.LastSeen.objects.create(user_id=user.id, room=chat_room)
            if user.id != course['trainer_id']:
                models.LastSeen.objects.create(user_id=course['trainer_id'], room=chat_room)
        
        serializer = serializers.ChatRoomSerializer(chat_room, context={'request': request})
        return Response(serializer.data)

    # Fetch all chat rooms for the user
    chat_rooms = models.ChatRoom.objects.filter(user_ids__contains=[user.id])
    serializer = serializers.ChatRoomSerializer(chat_rooms, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def create_chat_room(request):
    user = request.user
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    recipient_id = request.data.get('recipient_id')
    booking_session_id = request.data.get('booking_session_id')

    if not recipient_id and not booking_session_id:
        return Response({"success": False, "message": "Recipient ID or booking session ID required"}, status=400)

    user_ids = [user.id, recipient_id] if recipient_id else [user.id]
    if booking_session_id:
        booking_response = requests.get(
            f"http://localhost:8000/api/course/booking/{booking_session_id}/",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if booking_response.status_code != 200:
            return Response({"success": False, "message": "Booking session not found"}, status=400)
        booking_session = booking_response.json()
        course_response = requests.get(
            f"http://localhost:8000/api/course/course/{booking_session['course']['id']}/",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if course_response.status_code != 200:
            return Response({"success": False, "message": "Course not found"}, status=400)
        course = course_response.json()
        user_ids = [user.id, course['trainer_id']] if user.id != course['trainer_id'] else [user.id]

    chat_room = models.ChatRoom.objects.create(
        user_ids=user_ids,
        booking_session_id=booking_session_id
    )
    models.LastSeen.objects.create(user_id=user.id, room=chat_room)
    if recipient_id and user.id != recipient_id:
        models.LastSeen.objects.create(user_id=recipient_id, room=chat_room)

    serializer = serializers.ChatRoomSerializer(chat_room, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def get_messages(request, room_id):
    user = request.user
    try:
        chat_room = models.ChatRoom.objects.get(id=room_id)
        if user.id not in chat_room.user_ids:
            return Response({"success": False, "message": "You are not a member of this chat room"}, status=403)
        
        last_seen = models.LastSeen.objects.get(user_id=user.id, room=chat_room)
        last_seen.last_seen = timezone.now()
        last_seen.save()

        serializer = serializers.MessageSerializer(chat_room.messages, many=True, context={'request': request})
        return Response(serializer.data)
    except models.ChatRoom.DoesNotExist:
        return Response({"success": False, "message": "Chat room not found"}, status=404)
    except models.LastSeen.DoesNotExist:
        return Response({"success": False, "message": "Last seen not found"}, status=404)

@api_view(['GET'])
def last_seen(request, room_id):
    user = request.user
    try:
        chat_room = models.ChatRoom.objects.get(id=room_id)
        if user.id not in chat_room.user_ids:
            return Response({"success": False, "message": "You are not a member of this chat room"}, status=403)
        
        last_seen = models.LastSeen.objects.get(user_id=user.id, room=chat_room)
        serializer = serializers.LastSeenSerializer(last_seen, context={'request': request})
        return Response(serializer.data)
    except models.ChatRoom.DoesNotExist:
        return Response({"success": False, "message": "Chat room not found"}, status=404)
    except models.LastSeen.DoesNotExist:
        return Response({"success": False, "message": "Last seen not found"}, status=404)
    