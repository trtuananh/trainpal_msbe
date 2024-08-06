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
            return Response({"success": True})
        else:
            return Response({"success": False, "message": f"Invalid Form"})

    return Response({"success": False, "message": f"Wrong method, expect: POST"})

# endregion


# region > Sport



# endregion


# region > Location

@login_required(login_url='api-login')
@api_view(['GET'])
def getLocations(request):
    user = request.user
    serializer = srl.LocationSerializer(user.location_set.all(), many=True)
    return Response(serializer.data)


@login_required(login_url='api-login')
@api_view(['POST'])
def addLocation(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    # request.data["user"] = user
    form = forms.LocationForm(request.data)
    if form.is_valid():
        location = form.save(commit=False)
        location.user = user
        location.save()
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "invalid form"})
    

@login_required(login_url='api-login')
@api_view(['GET'])
def deleteLocation(request, pk):
    user = request.user
    try:
        user.location_set.get(id=pk).delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)})

# endregion


# region > Payment

@login_required(login_url='api-login')
@api_view(['GET'])
def getPaymentMethods(request):
    user = request.user
    payment_methods = user.paymentmethod_set.all()
    data_list = []
    for method in payment_methods:
        data = srl.PaymentMethodSerializer(method, many=False).data

        print(method.payment_type)
        if method.payment_type == 'CD':
            data['info'] = srl.CarMethodSerializer(method.cardmethod, many=False).data
        elif method.payment_type == 'EB':
            data['info'] = srl.EBankingMethodSerializer(method.ebankingmethod, many=False).data
        
        data_list.append(data)
    return Response(data_list)
 

@login_required(login_url='api-login')
@api_view(['POST'])
def addPaymentMethods(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    form = forms.PaymentMethodForm({"payment_type": request.data["payment_type"]})
    if form.is_valid():
        payment_method = form.save(commit=False)
        payment_method.user = user
        payment_method.save()

        payment_info_form = None
        if payment_method.payment_type == "CD":
            payment_info_form = forms.CardMethodForm(request.data["info"])
        elif payment_method.payment_type == "EB":
            payment_info_form = forms.EBankingMethodForm(request.data["info"])

        if payment_info_form is not None and payment_info_form.is_valid():
            payment_info = payment_info_form.save(commit=False)
            payment_info.payment_method = payment_method
            payment_info.save()

        return Response({"success": True})
    else:
        return Response({"success": False, "message": "invalid form"})
    

@login_required(login_url='api-login')
@api_view(['GET'])
def deletePaymentMethod(request, pk):
    user = request.user
    try:
        user.paymentmethod_set.get(id=pk).delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)})
    

@login_required(login_url='api-login')
@api_view(['POST'])
def makePayment(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})
    
    sender = request.user
    form = forms.PaymentHistoryForm(request.data)
    if form.is_valid():
        payment_history = form.save(commit=False)
        payment_history.sender = sender
        payment_history.receiver = payment_history.receive_method.user
        payment_history.save()
        return Response({'success': True})
    
    else:
        return Response({"success": False, "message": "invalid form"})


@login_required(login_url='api-login')
@api_view(['GET'])
def getPaymentHistory(request):
    user = request.user
    serializer = srl.PaymentHistorySerializer(user.sending.all(), many=True)
    return Response(serializer.data)

# endregion


# region > Message

@login_required(login_url='api-login')
@api_view(['GET'])
def getChatRooms(request):
    user = request.user
    serializer = srl.ChatRoomSerializer(user.chatroom_set.all(), many=True)
    return Response(serializer.data)


@login_required(login_url='api-login')
@api_view(['POST'])
def createChatRoom(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    form = forms.ChatRoomForm(request.data)
    if form.is_valid():
        chatroom = form.save(commit=False)
        chatroom.save()
        chatroom.users.set([user.id] + request.data["users"])
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "invalid form"})


@login_required(login_url='api-login')
@api_view(['GET'])
def getMessages(request, pk):
    chatroom = request.user.chatroom_set.get(id=pk)
    serializer = srl.MessageSerializer(chatroom.message_set.all(), many=True)
    return Response(serializer.data)


@login_required(login_url='api-login')
@api_view(['POST'])
def sendMessage(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    try:
        user.chatroom_set.get(id=request.data["room"])
    except:
        return Response({"success": False, "message": f"Can't send to this Room"})
    
    form = forms.MessageForm(request.data)
    if form.is_valid():
        message = form.save(commit=False)
        message.sender = user
        message.save()
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "invalid form"})

# endregion


# region > Course

@api_view(['GET', 'POST'])
def getCourses(request):
    filter = {}
    if request.method == 'POST':
        filter = request.data

    serializer = srl.CourseSerializer(models.Course.objects.filter(**filter), many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getCourse(request, pk):
    serializer = srl.CourseSerializer(models.Course.objects.get(id=pk), many=False)
    return Response(serializer.data)


@login_required(login_url='api-login')
@api_view(['POST'])
def createCourse(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    if not user.isTrainer:
        return Response({"success": False, "message": f"You're not a trainer"})

    form = forms.CourseForm(request.data)
    if form.is_valid():
        course = form.save(commit=False)
        course.trainer = user
        course.save()
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "invalid form"})
    

@login_required(login_url='api-login')
@api_view(['POST'])
def updateCourse(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    try:
        course = user.course_set.get(id=request.data["id"])
        form = forms.CourseForm(request.data, instance=course)
        if form.is_valid():
            form.save()
            return Response({"success": True})
        else:
            return Response({"success": False, "message": "invalid form"})
    except Exception as e:
        return Response({"success": False, "message": str(e)})
    

@login_required(login_url='api-login')
@api_view(['GET'])
def deleteCourse(request, pk):
    user = request.user
    try:
        user.course_set.get(id=pk).delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)})

# endregion


# region > Training Session

@api_view(['GET'])
def getTrainingSessions(request):
    serializer = srl.TrainingSessionSerializer(models.TrainingSession.objects.all(), many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getTrainingSession(request, pk):
    serializer = srl.TrainingSessionSerializer(models.TrainingSession.objects.get(id=pk), many=False)
    return Response(serializer.data)


@login_required(login_url='api-login')
@api_view(['POST'])
def addTrainingSession(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    if not user.isTrainer:
        return Response({"success": False, "message": f"You're not a trainer"})

    form = forms.TrainingSessionForm(request.data)
    if form.is_valid():
        try:
            course = user.course_set.get(id=request.data["course"])
            training_session = form.save(commit=False)

            try:
                update_sessions = course.trainingsession_set.filter(start__gte=training_session.start, 
                                                                end__lte=training_session.end)
                print("add_start <= start < end <= add_end:", len(update_sessions))
                for update_session in update_sessions:
                    if update_session.state != "AV":
                        return Response({"success": False, "message": "Schedule conflict"})
                update_sessions.delete()
            except: 
                pass

            try:
                update_session = course.trainingsession_set.get(start__lt=training_session.start, 
                                                                end__gt=training_session.end)
                print("start < add_start < add_end < end")
                if update_session.state != "AV":
                    return Response({"success": False, "message": "Schedule conflict"})
                split_session = forms.TrainingSessionForm(request.data).save(commit=False)
                split_session.start = training_session.end
                split_session.end = update_session.end
                split_session.save()

                update_session.end = training_session.start
                update_session.save()
            except: 
                pass

            try:
                update_session = course.trainingsession_set.get(start__lt=training_session.start, 
                                                                end__gt=training_session.start)
                print("start < add_start < end <= add_end")
                if update_session.state != "AV":
                    return Response({"success": False, "message": "Schedule conflict"})
                update_session.end = training_session.start
                update_session.save()
            except: 
                pass

            try:
                update_session = course.trainingsession_set.get(start__lt=training_session.end, 
                                                                end__gt=training_session.end)
                print("add_start <= start < add_end < end")
                if update_session.state != "AV":
                    return Response({"success": False, "message": "Schedule conflict"})
                update_session.start = training_session.end
                update_session.save()
            except: 
                pass

            training_session.save()
            return Response({"success": True})
        except:
            return Response({"success": False, "message": "Can't add to this Course"})
    else:
        return Response({"success": False, "message": "invalid form"})


@login_required(login_url='api-login')
@api_view(['GET'])
def deleteTrainingSession(request, pk):
    user = request.user
    try:
        training_session = models.TrainingSession.objects.get(id=pk)
        if training_session.course.trainer == user:
            training_session.delete()
            return Response({"success": True})
        else:
            return Response({'success': False, "message": "Can't delete training session"})
    except Exception as e:
        return Response({"success": False, "message": str(e)})

# endregion


# region > Booking Session

@api_view(['GET'])
def getBookingSessions(request):
    user = request.user
    serializer = srl.BookingSessionSerializer(user.bookingsession_set.all(), many=True)
    return Response(serializer.data)


@api_view(['GET'])
def getBookingSession(request, pk):
    user = request.user
    serializer = srl.BookingSessionSerializer(user.bookingsession_set.get(id=pk), many=False)
    return Response(serializer.data)


@login_required(login_url='api-login')
@api_view(['POST'])
def addBookingSession(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user

    form = forms.BookingSessionForm(request.data)
    if form.is_valid():
        training_session = models.TrainingSession.objects.get(id=request.data["training_session"])
        ntrainees = training_session.bookingsession_set.count()
        if ntrainees >= training_session.course.max_trainee:
            return Response({"success": False, "message": "Training Session is full"})

        booking_session = form.save(commit=False)
        booking_session.user = user
        booking_session.save()
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "invalid form"})


@login_required(login_url='api-login')
@api_view(['GET'])
def deleteBookingSession(request, pk):
    user = request.user
    try:
        user.bookingsession_set.get(id=pk).delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)})
 
# endregion


# region > Rating

@login_required(login_url='api-login')
@api_view(['POST'])
def addRating(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    form = forms.RatingForm(request.data)
    if form.is_valid():
        rating = form.save(commit=False)
        rating.user = user
        rating.save()
        return Response({"success": True})
    else:
        return Response({"success": False, "message": "invalid form"})
    

@api_view(['GET'])
def getRatings(request, course_pk):
    rating = models.Course.objects.get(id=course_pk).rating_set
    serializer = srl.RatingSerializer(rating, many=True)
    return Response(serializer.data)

# endregion
