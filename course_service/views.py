import os
import requests
import json
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.utils import OperationalError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from dateutil import parser
from . import models
from . import serializers
from . import forms

def convert_value_type(value):
    if type(value) is not str:
        return value
    try:
        return json.loads(value)
    except:
        return value

def convert_data_type(request_data):
    data = {}
    for key, value in request_data.items():
        data[key] = convert_value_type(value)
    return data

def get_form_errors(form):
    error_messages = []
    for field, errors in form.errors.items():
        for error in errors:
            error_messages.append(f"{field}: {error}")
    return ". ".join(error_messages)

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
def get_courses(request):
    trainer_id = request.GET.get('trainer')
    sport = request.GET.get('sport')
    latlng = request.GET.get('latlng')
    radius = request.GET.get('radius')
    page = request.GET.get('page')
    COURSES_PER_PAGE = 10
    DEFAULT_RADIUS = 10000

    courses = models.Course.objects.all()
    if trainer_id:
        courses = courses.filter(trainer_id=trainer_id)
    if sport:
        courses = courses.filter(sport=sport)
    if latlng:
        lat, lng = (float(i) for i in latlng.split(','))
        radius = float(radius) if radius else DEFAULT_RADIUS
        courses = courses.exclude(location=None).extra(
            select={'distance': 
                """
                6371 * acos(
                    cos(radians(%s)) * cos(radians(base_location.lat)) *
                    cos(radians(base_location.lng) - radians(%s)) +
                    sin(radians(%s)) * sin(radians(base_location.lat))
                )
                """
            },
            select_params=[lat, lng, lat],
            where=[
                """
                6371 * acos(
                    cos(radians(%s)) * cos(radians(base_location.lat)) *
                    cos(radians(base_location.lng) - radians(%s)) +
                    sin(radians(%s)) * sin(radians(base_location.lat))
                ) < %s
                """
            ],
            params=[lat, lng, lat, radius/1000],
            tables=['course_service_location']
        ).order_by('distance')

    if page:
        page = int(page)
        if page > courses.count() // COURSES_PER_PAGE:
            return Response({"success": False, "message": "Page out of range"}, status=400)
        courses = courses.order_by('-id')[page*COURSES_PER_PAGE:(page+1)*COURSES_PER_PAGE]

    serializer = serializers.CourseSerializer(courses, many=True, context={'request': request})
    return Response(status=200, data=serializer.data)

@api_view(['GET'])
def get_course(request, pk):
    serializer = serializers.CourseSerializer(
        models.Course.objects.get(id=pk), 
        many=False, 
        context={'request': request}
    )
    return Response(serializer.data)

@api_view(['POST'])
def create_course(request):
    if request.method != 'POST':
        return Response({"success": False, "message": "Wrong method, expect: POST"}, status=400)

    user = request.user
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    if not check_user_is_trainer(user.id, access_token):
        return Response({"success": False, "message": "You're not a trainer"}, status=400)

    data = convert_data_type(request.data)
    location = data.pop("location", None)
    form = forms.CourseForm(data)
    if form.is_valid():
        try:
            course = form.save(commit=False)
            course.trainer_id = user.id
            if 'image' in request.FILES:
                image = request.FILES['image']
                file_path = os.path.join(settings.MEDIA_ROOT, image.name)
                with open(file_path, 'wb+') as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                course.image = image.name
            course.save()
            if location is not None:
                location_form = forms.LocationForm(location)
                if not location_form.is_valid():
                    return Response({"success": False, "message": get_form_errors(location_form)}, status=400)
                location = location_form.save(commit=False)
                location.course = course
                location.save()
            serializer = serializers.CourseSerializer(course, many=False, context={'request': request})
            return Response({"success": True, "course": serializer.data})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=400)
    else:
        return Response({"success": False, "message": get_form_errors(form)}, status=400)

@api_view(['POST'])
def update_course(request):
    if request.method != 'POST':
        return Response({"success": False, "message": "Wrong method, expect: POST"}, status=400)

    user = request.user
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    data = convert_data_type(request.data)
    location = data.pop("location", None)
    course = models.Course.objects.get(id=data["id"])
    if course.trainer_id != user.id:
        return Response({"success": False, "message": "You're not the trainer of this course"}, status=400)

    form = forms.CourseForm(data, instance=course)
    if form.is_valid():
        try:
            if 'image' in request.FILES:
                image = request.FILES['image']
                file_path = os.path.join(settings.MEDIA_ROOT, image.name)
                with open(file_path, 'wb+') as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                course.image = image.name
            course.save()
            form.save()
            if location is not None:
                if hasattr(course, 'location') and course.location:
                    course.location.delete()
                location_form = forms.LocationForm(location)
                if not location_form.is_valid():
                    return Response({"success": False, "message": get_form_errors(location_form)}, status=400)
                location = location_form.save(commit=False)
                location.course = course
                location.save()
            serializer = serializers.CourseSerializer(course, many=False, context={'request': request})
            return Response({"success": True, "course": serializer.data})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=400)
    else:
        return Response({"success": False, "message": get_form_errors(form)}, status=400)

@api_view(['GET'])
def delete_course(request, pk):
    user = request.user
    try:
        course = models.Course.objects.get(id=pk)
        if course.trainer_id != user.id:
            return Response({"success": False, "message": "You're not the trainer of this course"}, status=400)
        course.delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=400)

@api_view(['GET'])
def get_training_sessions(request):
    user = request.user
    course_id = request.GET.get('course_id')
    from_date = request.GET.get('from') 
    to_date = request.GET.get('to')
    page = request.GET.get('page')
    booked = request.GET.get('booked')
    reverse = request.GET.get('reverse')
    SESSIONS_PER_PAGE = 10

    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    is_trainer = check_user_is_trainer(user.id, access_token)

    if course_id:
        training_sessions = models.TrainingSession.objects.filter(course_id=course_id)
    elif is_trainer:
        training_sessions = models.TrainingSession.objects.filter(course__trainer_id=user.id)
    else:
        training_sessions = models.TrainingSession.objects.all()

    if from_date:
        training_sessions = training_sessions.filter(start__gte=parser.isoparse(from_date))
    if to_date:
        training_sessions = training_sessions.filter(end__lte=parser.isoparse(to_date))
    if booked:
        training_sessions = training_sessions.exclude(booking_sessions=None)
    if reverse:
        training_sessions = training_sessions.order_by('-start')
    else:
        training_sessions = training_sessions.order_by('start')

    if page:
        page = int(page)
        if page > training_sessions.count() // SESSIONS_PER_PAGE:
            return Response({"success": False, "message": "Page out of range"}, status=400)
        training_sessions = training_sessions[page * SESSIONS_PER_PAGE:(page + 1) * SESSIONS_PER_PAGE]

    serializer = serializers.TrainingSessionSerializer(training_sessions, context={'request': request}, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_training_session(request, pk):
    user = request.user
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    is_trainer = check_user_is_trainer(user.id, access_token)

    if is_trainer:
        training_session = models.TrainingSession.objects.get(id=pk)
        if training_session.course.trainer_id != user.id:
            return Response({"success": False, "message": "You're not the trainer of this course"}, status=400)
    else:
        booking_session = models.BookingSession.objects.get(id=pk)
        if booking_session.user_id != user.id:
            return Response({"success": False, "message": "You're not the user of this booking session"}, status=400)
        training_session = booking_session.training_session

    serializer = serializers.TrainingSessionDetailSerializer(training_session, many=False, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def add_training_session(request):
    if request.method != 'POST':
        return Response({"success": False, "message": "Wrong method, expect: POST"}, status=400)

    user = request.user
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    if not check_user_is_trainer(user.id, access_token):
        return Response({"success": False, "message": "You're not a trainer"}, status=400)

    form = forms.TrainingSessionForm(request.data)
    if form.is_valid():
        try:
            course = models.Course.objects.get(id=request.data["course"], trainer_id=user.id)
            training_session = form.save(commit=False)
            update_sessions = course.training_sessions.filter(start__gte=training_session.start, end__lte=training_session.end)
            for update_session in update_sessions:
                if update_session.booking_sessions.count() > 0:
                    return Response({"success": False, "message": "Schedule conflict"}, status=400)
            update_sessions.delete()

            try:
                update_session = course.training_sessions.get(start__lt=training_session.start, end__gt=training_session.end)
                if update_session.booking_sessions.count() > 0:
                    return Response({"success": False, "message": "Schedule conflict"}, status=400)
                split_session = forms.TrainingSessionForm(request.data).save(commit=False)
                split_session.start = training_session.end
                split_session.end = update_session.end
                split_session.save()
                update_session.end = training_session.start
                update_session.save()
            except:
                pass

            try:
                update_session = course.training_sessions.get(start__lt=training_session.start, end__gt=training_session.start)
                if update_session.booking_sessions.count() > 0:
                    return Response({"success": False, "message": "Schedule conflict"}, status=400)
                update_session.end = training_session.start
                update_session.save()
            except:
                pass

            try:
                update_session = course.training_sessions.get(start__lt=training_session.end, end__gt=training_session.end)
                if update_session.booking_sessions.count() > 0:
                    return Response({"success": False, "message": "Schedule conflict"}, status=400)
                update_session.start = training_session.end
                update_session.save()
            except:
                pass

            training_session.save()
            return Response({"success": True}, status=200)
        except:
            return Response({"success": False, "message": "Can't add to this Course"}, status=400)
    else:
        return Response({"success": False, "message": get_form_errors(form)}, status=400)

@api_view(['GET'])
def delete_training_session(request, pk):
    user = request.user
    try:
        training_session = models.TrainingSession.objects.get(id=pk)
        if training_session.course.trainer_id != user.id:
            return Response({"success": False, "message": "You're not the trainer of this course"}, status=400)
        training_session.delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=400)

def check_booking_sessions(booking_sessions):
    booking_sessions = list(booking_sessions)
    booking_sessions.sort(key=lambda x: x.start)
    for i, booking_session in enumerate(booking_sessions):
        course = booking_session.course
        if i > 0 and booking_session.start < booking_sessions[i-1].end:
            return False
        try:
            training_session = course.training_sessions.get(start__lte=booking_session.start, end__gte=booking_session.end)
            if training_session.booking_sessions.count() >= course.max_trainee:
                return False
        except:
            return False
    return True

def add_training_session(booking_session, locked_training_sessions):
    course = booking_session.course
    start = booking_session.start
    end = booking_session.end
    data = {"course": course, "start": start, "end": end}
    form = forms.TrainingSessionForm(data)
    if not form.is_valid():
        return None
    try:
        try:
            update_session = locked_training_sessions.get(start__eq=start, end__eq=end)
            if update_session.booking_sessions.count() >= course.max_trainee:
                return None
            return update_session
        except:
            pass
        training_session = form.save(commit=False)
        try:
            update_sessions = locked_training_sessions.filter(start__gte=start, end__lte=end)
            for update_session in update_sessions:
                if update_session.booking_sessions.count() > 0:
                    return None
            update_sessions.delete()
        except:
            pass
        try:
            update_session = locked_training_sessions.get(start__lt=start, end__gt=end)
            if update_session.booking_sessions.count() > 0:
                return None
            split_session = forms.TrainingSessionForm(form.data).save(commit=False)
            split_session.start = training_session.end
            split_session.end = update_session.end
            split_session.save()
            update_session.end = training_session.start
            update_session.save()
        except:
            pass
        try:
            update_session = locked_training_sessions.get(start__lt=start, end__gt=start)
            if update_session.booking_sessions.count() > 0:
                return None
            update_session.end = training_session.start
            update_session.save()
        except:
            pass
        try:
            update_session = locked_training_sessions.get(start__lt=end, end__gt=end)
            if update_session.booking_sessions.count() > 0:
                return None
            update_session.start = end
            update_session.save()
        except:
            pass
        training_session.save()
        return training_session
    except:
        return None

def get_booking_to_locked_training_sessions(booking_sessions, timeout=30):
    booking_to_locked_training_sessions = {}
    try:
        for booking_session in booking_sessions:
            course = booking_session.course
            start = booking_session.start
            end = booking_session.end
            locked_training_sessions = course.training_sessions.select_for_update().filter(
                start__lte=end,
                end__gte=start
            )
            booking_to_locked_training_sessions[booking_session] = locked_training_sessions
    except OperationalError:
        raise Exception("Database busy, please try again")
    return booking_to_locked_training_sessions

def try_to_add_training_sessions(booking_sessions, timeout=30):
    booking_to_locked_training_sessions = {}
    with transaction.atomic():
        booking_to_locked_training_sessions = get_booking_to_locked_training_sessions(booking_sessions, timeout)
        if not check_booking_sessions(booking_sessions):
            raise Exception("Booking sessions are not valid")
        booking_to_training_sessions = {}
        for booking_session, locked_training_sessions in booking_to_locked_training_sessions.items():
            training_session = add_training_session(booking_session, locked_training_sessions)
            if training_session is None:
                raise Exception("Can't add training session")
            booking_to_training_sessions[booking_session] = training_session
        return booking_to_training_sessions

@api_view(['GET'])
def get_booking_sessions(request):
    user = request.user
    from_date = request.GET.get('from') 
    to_date = request.GET.get('to')
    page = request.GET.get('page')
    reverse = request.GET.get('reverse')
    SESSIONS_PER_PAGE = 10

    booking_sessions = models.BookingSession.objects.filter(user_id=user.id)
    if from_date:
        booking_sessions = booking_sessions.filter(start__gte=parser.isoparse(from_date))
    if to_date:
        booking_sessions = booking_sessions.filter(end__lte=parser.isoparse(to_date))
    booking_sessions = booking_sessions.exclude(training_session=None)
    if reverse:
        booking_sessions = booking_sessions.order_by('-start')
    else:
        booking_sessions = booking_sessions.order_by('start')

    if page:
        page = int(page)
        if page > booking_sessions.count() // SESSIONS_PER_PAGE:
            return Response({"success": False, "message": "Page out of range"}, status=400)
        booking_sessions = booking_sessions[page * SESSIONS_PER_PAGE:(page + 1) * SESSIONS_PER_PAGE]

    serializer = serializers.BookingSessionSerializer(booking_sessions, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def get_booking_session(request, pk):
    user = request.user
    serializer = serializers.BookingSessionSerializer(
        models.BookingSession.objects.get(id=pk, user_id=user.id), 
        many=False, 
        context={'request': request}
    )
    return Response(serializer.data)

@api_view(['POST'])
def add_booking_session(request):
    if request.method != 'POST':
        return Response({"success": False, "message": "Wrong method, expect: POST"}, status=400)

    user = request.user
    form = forms.BookingSessionForm(request.data)
    if form.is_valid():
        training_session = models.TrainingSession.objects.get(id=request.data["training_session"])
        ntrainees = training_session.booking_sessions.count()
        if ntrainees >= training_session.course.max_trainee:
            return Response({"success": False, "message": "Training Session is full"}, status=400)
        booking_session = form.save(commit=False)
        booking_session.user_id = user.id
        booking_session.save()
        return Response({"success": True}, status=200)
    else:
        return Response({"success": False, "message": get_form_errors(form)}, status=400)

@api_view(['GET'])
def delete_booking_session(request, pk):    
    user = request.user
    try:
        booking_session = models.BookingSession.objects.get(id=pk, user_id=user.id)
        booking_session.delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=400)

@api_view(['POST'])
def add_rating(request):
    if request.method != 'POST':
        return Response({"success": False, "message": "Wrong method, expect: POST"}, status=400)

    user = request.user
    form = forms.RatingForm(request.data)
    if form.is_valid():
        rating = form.save(commit=False)
        rating.user_id = user.id
        rating.save()
        return Response({"success": True})
    else:
        return Response({"success": False, "message": get_form_errors(form)}, status=400)

@api_view(['GET'])
def get_ratings(request, course_pk):
    ratings = models.Course.objects.get(id=course_pk).ratings
    serializer = serializers.RatingSerializer(ratings, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_booking_sessions_by_payment(request, payment_id):
    booking_sessions = models.BookingSession.objects.filter(payment_id=payment_id)
    serializer = serializers.BookingSessionSerializer(booking_sessions, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def update_booking_session(request, pk):
    user = request.user
    data = request.data
    try:
        booking_session = models.BookingSession.objects.get(id=pk, user_id=user.id)
        if 'payment_id' in data:
            booking_session.payment_id = data['payment_id']
        if 'training_session' in data:
            booking_session.training_session_id = data['training_session']
        booking_session.save()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=400)
