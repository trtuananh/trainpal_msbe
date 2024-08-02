from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

import json

from base import models
from base import forms
# from .serializers import RoomSerializer
from base.api import serializers as srl


@api_view(['GET'])
def getRoutes(request):
    routes = [
        'GET /api',

        'POST /api/login',
        'GET /api/logout',
        'POST /api/register',
    ]
    return Response(routes)


# region > Authentication

@api_view(['POST'])
def loginUser(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    data = request.data
    username = data["username"].lower()
    password = data["password"]

    try:
        user = models.User.objects.get(username=username)
    except:
        return Response({"success": False, "message": "Invalid username"})

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "Wrong password!"})


@api_view(['GET'])
def logoutUser(request):
    logout(request)
    return Response({"success": True})


@api_view(['POST'])
def registerUser(request):
    form = forms.MyUserCreationForm()

    if request.method == 'POST':
        form = forms.MyUserCreationForm(request.data)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return Response({"success": True})
        else:
            return Response({"success": False, "message": "invalid form"})

    return Response({"success": False, "message": f"Wrong method, expect: POST"})

# endregion

# region > User

@api_view(['GET'])
def userProfile(request, pk):
    user = models.User.objects.get(id=pk)
    serializer = srl.UserSerializer(user, many=False)
    return Response(serializer.data)


@login_required(login_url='api-login')
@api_view(['POST'])
def updateProfile(request):
    user = request.user

    if request.method == 'POST':
        form = forms.UserForm(request.data, instance=user)
        if form.is_valid():
            form.save()
            serializer = srl.UserSerializer(user, many=False)
            return Response(serializer.data)
        else:
            return Response({"success": False, "message": f"Invalid Form"})

    return Response({"success": False, "message": f"Wrong method, expect: POST"})

# endregion

# region > Location

@login_required(login_url='api-login')
@api_view(['GET'])
def getLocations(request):
    user = request.user
    serializer = srl.LocationSerializer(user.location_set.all(), many=True)
    return Response(serializer.data).


@login_required(login_url='api-login')
@api_view(['POST'])
def addLocation(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    form = forms.LocationForm(request.data)
    if form.is_valid():
        form.save()
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "invalid form"})

# endregion


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
