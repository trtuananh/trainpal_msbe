from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from . import models
from . import forms


def loginPage(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        try:
            user = models.User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username OR password does not exit')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = forms.MyUserCreationForm()

    if request.method == 'POST':
        form = forms.MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html', {'form': form})


@login_required(login_url='login')
def home(request):
    user = request.user
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = user.chatroom_set.filter(name__icontains=q)

    topics = models.Sport.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = models.Message.objects.all()[0:3]

    context = {'rooms': rooms, 'room_count': room_count, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/home.html', context)


def room(request, pk):
    room = models.ChatRoom.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.users.all()

    if request.method == 'POST':
        message = models.Message.objects.create(
            sender=request.user,
            room=room,
            content=request.POST.get('body')
        )
        room.users.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = models.User.objects.get(id=pk)
    form = forms.UserForm(instance=user)
    sports = user.sports.all()
    rooms = user.chatroom_set.all()
    room_messages = user.message_set.all()
    context = {'user': user, 'rooms': rooms, 'topics': sports,
               'room_messages': room_messages, 'form': form}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = forms.UserForm(instance=user)

    if request.method == 'POST':
        form = forms.UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    return render(request, 'base/update-user.html', {'form': form})


@login_required(login_url='login')
def createRoom(request):
    form = forms.ChatRoomForm()
    if request.method == 'POST':

        user = request.user
        form = forms.ChatRoomForm(request.POST)
        if form.is_valid():
            chatroom = form.save(commit=False)
            chatroom.host = user
            chatroom.save()
            chatroom.users.set([user.id] + [int(request.POST.get("users"))])
            return redirect('home')
        else:
            messages.error(request, 'Invalid Form')

    context = {'form': form}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = models.ChatRoom.objects.get(id=pk)
    form = forms.ChatRoomForm(instance=room)
    user = request.user
    if user != room.host:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        if form.is_valid():
            chatroom = form.save(commit=False)
            chatroom.host = user
            chatroom.save()
            chatroom.users.set([user.id] + [int(request.POST.get("users"))])
            return redirect('home')
        else:
            messages.error(request, 'Invalid Form')

    context = {'form': form, 'room': room}
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = models.ChatRoom.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = models.Message.objects.get(id=pk)

    if request.user != message.sender:
        return HttpResponse('Your are not allowed here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})


def topicsPage(request):
    # q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = models.Sport.objects.all()
    return render(request, 'base/topics.html', {'topics': topics})


def activityPage(request):
    room_messages = models.Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages': room_messages})
