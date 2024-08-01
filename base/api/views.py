from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib import auth
import json

from base import models
# from .serializers import RoomSerializer
from base.api import serializers


@api_view(['GET'])
def getRoutes(request):
    routes = [
        'GET /api',

        'POST /api/login',
        'GET /api/logout',
        'POST /api/register',
    ]
    return Response(routes)


@api_view(['POST'])
def loginUser(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    data = request.data
    email = data["email"].lower()
    password = data["password"]

    try:
        user = models.User.objects.get(email=email)
    except:
        return Response({"success": False, "message": "Invalid email"})

    user = auth.authenticate(request, email=email, password=password)

    if user is not None:
        auth.login(request, user)
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "Wrong password!"})


@api_view(['GET'])
def getRooms(request):
    rooms = Room.objects.all()
    serializer = RoomSerializer(rooms, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getRoom(request, pk):
    room = Room.objects.get(id=pk)
    serializer = RoomSerializer(room, many=False)
    return Response(serializer.data)
