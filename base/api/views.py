import os
import numpy as np
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta
from dateutil import parser
from django.conf import settings

from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from rest_framework_simplejwt.tokens import RefreshToken  # Thêm import này ở đầu file
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from django.db import transaction
from django.db.utils import OperationalError
from django.db.models import Count
import json
import requests

from base import models
from base import forms      
# from .serializers import RoomSerializer
from base.api import serializers as srl


def convert_value_type(value):
    if type(value) is not str:
        return value

    # Xử lý null
    # if value == "null":
    #     return None
        
    # # Thử chuyển sang số nguyên
    # try:
    #     if str(int(value)) == value:
    #         return int(value)
    # except ValueError:
    #     pass
    
    # # Thử chuyển sang số thực
    # try:
    #     return float(value)
    # except ValueError:
    #     pass
    
    # # Xử lý boolean
    # if value.lower() == "true":
    #     return True
    # if value.lower() == "false":
    #     return False
    try:
        return json.loads(value)
    except:
        # Giữ nguyên giá trị string nếu không khớp các kiểu trên
        return value

    # return value


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
    error_string = ". ".join(error_messages)

    return error_string


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
        return Response({"success": False, "message": f"Wrong method, expect: POST"}, status=400)

    data = request.data
    username = data["username"]
    password = data["password"]

    if not models.User.objects.filter(username=username).exists():
        try:
            username = models.User.objects.get(email=username).username
        except:
            print("Invalid username", username)
            return Response({"success": False, "message": "Invalid username"}, status=401)

    try:
        print("username", username)
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # Tạo token cho user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "success": True,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                },
                "user_id": user.id
            })
        else:
            return Response({"success": False, "message": "Wrong password!"})
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=401)


@api_view(['GET'])
def logoutUser(request):
    logout(request)
    return Response({"success": True})


@api_view(['POST'])
def registerUser(request):
    form = forms.MyUserCreationForm()

    if request.method == 'POST':
        print(request.data)

        username = request.data.get("username")
        if models.User.objects.filter(username=username).exists():
            return Response({"success": False, "message": "Username already exists"}, status=400)
        
        email = request.data.get("email")
        if models.User.objects.filter(email=email).exists():
            return Response({"success": False, "message": "Email already exists"}, status=400)

        form = forms.MyUserCreationForm(request.data)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username
            user.save()
            login(request, user)
            # Tạo token cho user
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "success": True,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token)
                },
                "user_id": user.id
            })
        else:
            print("Form errors:", get_form_errors(form)) 
            return Response({"success": False, "message": get_form_errors(form)}, status=400)

    return Response({"success": False, "message": f"Wrong method, expect: POST"}, status=400)


class TokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')
        # device_id = request.data.get('device_id')
        
        try:
            if not refresh_token:
                return Response({"success": False, "message": "Refresh token is required"}, status=400)
            
            # Tạo token mới
            refresh = RefreshToken(refresh_token)
            access = str(refresh.access_token)
            
            # Cập nhật last_used
            # device.save()  # This updates last_used due to auto_now
            
            return Response({
                'access': access,
                'refresh': refresh_token  # Giữ nguyên refresh token
            })
        except Exception as e:
            return Response(
                {'message': str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )

# endregion


# region > User

@api_view(['GET'])
def userProfile(request, pk):
    user = models.User.objects.get(id=pk)
    serializer = srl.UserSerializer(user, many=False, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def updateProfile(request):
    user = request.user

    data = convert_data_type(request.data)
    print(data)
    if user.id != data["id"]:
        return Response({"success": False, "message": "You are not allowed to update this profile"}, status=400)

    if request.method == 'POST':
        try:
            form = forms.UserForm(data, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                return Response(srl.UserSerializer(user, many=False, context={'request': request}).data)
            else:
                return Response({"success": False, "message": get_form_errors(form)}, status=400)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=400)

    return Response({"success": False, "message": f"Wrong method, expect: POST"}, status=400)

# endregion


# region > Sport



# endregion


# region > Location

@login_required(login_url='api-login')
@api_view(['GET'])
def getLocations(request):
    user = request.user
    serializer = srl.LocationSerializer(user.locations.all(), many=True)
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
        return Response({"success": False, "message": get_form_errors(form)}, status=400)
    

@login_required(login_url='api-login')
@api_view(['GET'])
def deleteLocation(request, pk):
    user = request.user
    try:
        user.locations.get(id=pk).delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)})

# endregion


# region > Momo Payment

PAYMENT_PER_PAGE = 20


@api_view(['GET'])
def getPayments(request):
    user = request.user
    page = request.GET.get('page')
    now = timezone.now()

    if user.isTrainer:
        payments = models.Payment.objects.filter(receiver=user).exclude(
            payment_method='OFF',
            booking_sessions__end__gte=now
        )
    else:
        payments = models.Payment.objects.filter(sender=user).exclude(
            payment_method='OFF',
            booking_sessions__end__gte=now
        )

    payments = payments.order_by('-updated')

    if page:
        page = int(page)
        n_pages = len(payments) // PAYMENT_PER_PAGE
        if page > n_pages:
            return Response({"success": False, "message": "Page out of range"}, status=400)
        payments = payments[page * PAYMENT_PER_PAGE:(page + 1) * PAYMENT_PER_PAGE]

    serializer = srl.PaymentSerializer(payments, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def getPayment(request, pk):
    user = request.user
    payment = models.Payment.objects.get(id=pk)
    if user.isTrainer:
        if payment.receiver != user:
            return Response({"success": False, "message": "You are not the receiver of this payment"}, status=400)
    else:
        if payment.sender != user:
            return Response({"success": False, "message": "You are not the sender of this payment"}, status=400)
    serializer = srl.PaymentSerializer(payment, many=False, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
def createPayment(request):
    user = request.user
    try:
        course = models.Course.objects.get(id=request.data["course"])
        sessions = request.data["sessions"]
        payment_method = request.data["payment_method"]
        order_info = request.data.get("order_info")
        redirect_url = request.data.get("redirect_url")
        ipn_url = request.data.get("ipn_url")
        lang = request.data.get("lang")
        total_price = 0
        booking_sessions = []

        for session in sessions:
            start = parser.isoparse(session["start"])
            end = parser.isoparse(session["end"])
            price = course.unit_price * (end - start).total_seconds() / (3600 * course.unit_session)
            total_price += price
            booking_sessions.append(models.BookingSession.objects.create(
                user=user, 
                price=price, 
                start=start, 
                end=end,
                course=course
            ))

        if not check_booking_sesssions(booking_sessions):
            for booking_session in booking_sessions:
                booking_session.delete()
            return Response({
                "success": False, 
                "message": "Sessions are not available"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Tạo payment history với trạng thái pending
        if payment_method == "ONL":
            payment_id = str(uuid.uuid4()).replace("-", "")
            momo_response = MomoAPI.create_payment(
                int(total_price), 
                payment_id, 
                order_info=order_info,
                redirect_url=redirect_url, 
                ipn_url=ipn_url,
                lang=lang
            )
            if momo_response.get("resultCode") != 0:
                return Response({
                    "success": False,
                    "message": momo_response.get("message")
                }, status=status.HTTP_400_BAD_REQUEST)

            payment = models.Payment.objects.create(
                payment_id=payment_id,
                sender=user,
                receiver=course.trainer,
                payment_method=payment_method,
                value=total_price,
                is_paid=False
            )

            for booking_session in booking_sessions:
                booking_session.payment = payment
                booking_session.save()

            response = srl.PaymentSerializer(payment, many=False, context={'request': request}).data
            response["payUrl"] = momo_response.get("payUrl") if momo_response else ""
            return Response(response)

        else: # offline payment
            booking_to_training_sessions = try_to_add_training_sessions(booking_sessions)

            payments = []
            for booking_session, training_session in booking_to_training_sessions.items():
                payment = models.Payment.objects.create(
                    payment_id=str(uuid.uuid4()),
                    sender=user,
                    receiver=course.trainer,
                    payment_method=payment_method,
                    value=booking_session.price,
                    is_paid=True,
                    success=True,
                )
                payments.append(payment)

                booking_session.payment = payment
                booking_session.training_session = training_session
                booking_session.save()

            response = srl.PaymentSerializer(payments, many=True, context={'request': request}).data
            return Response(response)

    except Exception as e:
        # Nếu có lỗi, xóa tất cả booking sessions và payment history đã tạo
        if 'payment' in locals():
            payment.delete()
        elif 'payments' in locals():
            for payment in payments:
                payment.delete()
        return Response({
            "success": False,
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def momoPaymentCallback(request):
    print("Momo callback from:", request.data)
    """Callback API để nhận thông báo từ Momo"""
    accessKey = MomoAPI.accessKey
    amount = request.data.get('amount')
    extraData = request.data.get('extraData')
    message = request.data.get('message')
    orderId = request.data.get('orderId')
    orderInfo = request.data.get('orderInfo')
    orderType = request.data.get('orderType')
    partnerCode = MomoAPI.partnerCode
    payType = request.data.get('payType')
    requestId = request.data.get('requestId')
    responseTime = request.data.get('responseTime')
    resultCode = request.data.get('resultCode')
    transId = request.data.get('transId')
    # Không thể đảo ngược thuật toán sha256 để decode signature về dạng rawString
    # Vì vậy, chúng ta sẽ mã hóa lại dữ liệu để so sánh với signature nhận được

    expectedSignature = MomoAPI.get_signature(
        accessKey=accessKey,
        amount=amount,
        extraData=extraData,
        message=message,
        orderId=orderId,
        orderInfo=orderInfo,
        orderType=orderType,
        partnerCode=partnerCode,
        payType=payType,
        requestId=requestId,
        responseTime=responseTime,
        resultCode=resultCode,
        transId=transId
    )
    
    signature = request.data.get('signature')
    # So sánh signature nhận được với signature dự kiến
    if signature != expectedSignature:
        return Response({
            "success": False,
            "message": "Signature không khớp"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        payment = models.Payment.objects.get(payment_id=orderId)
        if payment.is_paid:
            print("Payment already processed")
            response = srl.PaymentSerializer(payment, many=False, context={'request': request}).data
            return Response(response)
        
        if int(resultCode) == 0:
            print("Still processing")
            # Cập nhật trạng thái payment history
            payment.is_paid = True
            payment.momo_transaction_id = transId
            payment.momo_payment_type = payType

            booking_sessions = payment.booking_sessions.all()
            booking_to_training_sessions = try_to_add_training_sessions(booking_sessions)

            for booking_session, training_session in booking_to_training_sessions.items():
                booking_session.training_session = training_session
                booking_session.save()

            payment.success = True      
        else:
            payment.message = message

        payment.save()
        response = srl.PaymentSerializer(payment, many=False, context={'request': request}).data
        return Response(response)
        
    except Exception as e:
        print("Error:", str(e))
        if 'payment' in locals():
            payment.success = False
            payment.message = "Sessions are not available"    
            payment.save()

        return Response({
            "success": False,
            "message": str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def momoPayment(request):
    amount = "50000"
    payment_id = str(uuid.uuid4())
    order_info = "pay with MoMo"
    response = MomoAPI.create_payment(amount, payment_id)
    return Response(response)


@api_view(['POST'])
def verifyMomoPayment(request):
    payment_id = request.data.get('orderId')
    response = MomoAPI.verify_payment(payment_id)
    return Response(response)


class MomoAPI:
    # endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
    accessKey = "F8BBA842ECF85"
    secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    orderInfo = "pay with MoMo"
    partnerCode = "MOMO"
    redirectUrl = "trainpal://home"
    ipnUrl = "https://trainpal.vn/api/momo/callback"
    # amount = "50000"
    # orderId = str(uuid.uuid4())
    # requestId = str(uuid.uuid4())
    extraData = ""  # pass empty value or Encode base64 JsonString
    partnerName = "TrainPal"
    requestType = "payWithMethod"
    storeId = "Test Store"
    orderGroupId = ""
    autoCapture = True
    lang = "vi"
    orderGroupId = ""

    # before sign HMAC SHA256 with format: accessKey=$accessKey&amount=$amount&extraData=$extraData&ipnUrl=$ipnUrl
    # &orderId=$orderId&orderInfo=$orderInfo&partnerCode=$partnerCode&redirectUrl=$redirectUrl&requestId=$requestId
    # &requestType=$requestType
    
    @staticmethod
    def create_payment(amount, payment_id, order_info=None, redirect_url=None, ipn_url=None, lang=None):
        endpoint = "https://test-payment.momo.vn/v2/gateway/api/create"
        accessKey = MomoAPI.accessKey
        secretKey = MomoAPI.secretKey
        partnerCode = MomoAPI.partnerCode
        redirectUrl = redirect_url if redirect_url else MomoAPI.redirectUrl
        ipnUrl = ipn_url if ipn_url else MomoAPI.ipnUrl
        extraData = MomoAPI.extraData
        partnerName = MomoAPI.partnerName
        requestType = MomoAPI.requestType
        storeId = MomoAPI.storeId
        autoCapture = MomoAPI.autoCapture
        lang = lang if lang else MomoAPI.lang
        orderGroupId = MomoAPI.orderGroupId
        
        orderId, requestId = payment_id, payment_id
        orderInfo = order_info if order_info else MomoAPI.orderInfo
        signature = MomoAPI.get_signature(
            accessKey=accessKey, 
            amount=amount, 
            extraData=extraData, 
            ipnUrl=ipnUrl, 
            orderId=orderId, 
            orderInfo=orderInfo, 
            partnerCode=partnerCode, 
            redirectUrl=redirectUrl, 
            requestId=requestId, 
            requestType=requestType)

        data = {
            'partnerCode': partnerCode,
            'orderId': orderId,
            'partnerName': partnerName,
            'storeId': storeId,
            'ipnUrl': ipnUrl,
            'amount': amount,
            'lang': lang,
            'requestType': requestType,
            'redirectUrl': redirectUrl,
            'autoCapture': autoCapture,
            'orderInfo': orderInfo,
            'requestId': requestId,
            'extraData': extraData,
            'signature': signature,
            'orderGroupId': orderGroupId
        }

        data = json.dumps(data)

        clen = len(data)
        response = requests.post(endpoint, data=data, headers={'Content-Type': 'application/json', 'Content-Length': str(clen)})
        return response.json()
    
    @staticmethod
    def verify_payment(payment_id):
        endpoint = "https://test-payment.momo.vn/v2/gateway/api/query"
        accessKey = MomoAPI.accessKey
        partnerCode = MomoAPI.partnerCode
        
        orderId, requestId = payment_id, payment_id
        signature = MomoAPI.get_signature(
            accessKey=accessKey, 
            orderId=orderId, 
            partnerCode=partnerCode, 
            requestId=requestId)

        data = {
            'partnerCode': partnerCode,
            'requestId': requestId,
            'orderId': orderId,
            'signature': signature,
            'lang': MomoAPI.lang,
        }

        data = json.dumps(data)

        response = requests.post(endpoint, data=data, headers={'Content-Type': 'application/json'})
        return response.json()

    @staticmethod
    def get_signature(**kwargs):
        params = []
        for key, value in kwargs.items():
            params.append(f"{key}={value}")
        rawSignature = "&".join(params)

        h = hmac.new(bytes(MomoAPI.secretKey, 'utf-8'), bytes(rawSignature, 'utf-8'), hashlib.sha256)
        signature = h.hexdigest()
        return signature

# endregion


# region > Message

@api_view(['GET'])
def getChatRoom(request):
    room_id = request.GET.get('room')
    receiver_id = request.GET.get('receiver')
    if room_id:
        room_id = int(room_id)
        try:
            chatroom = request.user.chat_rooms.get(id=room_id)
        except Exception as e:
            print(e)
            return Response({"success": False, "message": "You are not in this chat room"}, status=400)
    elif receiver_id:
        receiver_id = int(receiver_id)
        print("receiver_id:", receiver_id, type(receiver_id))
        chatrooms = models.ChatRoom.objects.annotate(
            user_count=Count('users')
        ).filter(
            users__id=request.user.id
        ).filter(
            users__id=receiver_id,
            user_count=2
        )
        print("chatrooms:", chatrooms.count(), chatrooms)
        if chatrooms.count() == 0:
            chatroom = models.ChatRoom.objects.create()
            chatroom.users.set([request.user.id, receiver_id])
        else:
            chatroom = chatrooms.first()
    else:
        serializer = srl.ChatRoomSerializer(
            request.user.chat_rooms.all(), 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
    
    serializer = srl.ChatRoomSerializer(chatroom, many=False, context={'request': request})
    print(serializer.data)
    return Response(serializer.data)


@api_view(['POST'])
def createChatRoom(request):
    if request.method != 'POST':
        return Response(
            {"success": False, "message": f"Wrong method, expect: POST"}, 
            status=400
        )

    user = request.user
    form = forms.ChatRoomForm(request.data)
    if form.is_valid():
        chatroom = form.save(commit=False)
        chatroom.users.set(set([user.id]) | set(request.data["users"]))
        chatroom.save()
        return Response(srl.ChatRoomSerializer(
            chatroom, many=False, context={'request': request}).data)
    else:
        return Response(
            {"success": False, "message": get_form_errors(form)}, 
            status=400
        )


MESSAGES_PER_PAGE = 20


@api_view(['GET'])
def getMessages(request):
    room_id = request.GET.get('room')
    page = request.GET.get('page')
    try:
        chatroom = request.user.chat_rooms.get(id=room_id)
    except:
        return Response(
            {"success": False, "message": "You are not in this chat room"}, 
            status=400
        )
    
    messages = chatroom.messages.all().order_by('-date')
    if page:
        page = int(page)
        if page > chatroom.messages.count() // MESSAGES_PER_PAGE:
            return Response(
                {"success": False, "message": "Page out of range"}, 
                status=400
            )
        messages = messages[page*MESSAGES_PER_PAGE:(page+1)*MESSAGES_PER_PAGE]

    serializer = srl.MessageSerializer(messages, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
def lastSeen(request):
    user = request.user
    room_id = request.GET.get('room')
    date = request.GET.get('last_seen')
    try:
        chatroom = user.chat_rooms.get(id=room_id)
    except:
        return Response({"success": False, "message": "You are not in this chat room"}, status=400)
    
    try:
        last_seen = user.last_seens.get(room=chatroom)
        last_seen.date = date
        last_seen.save()
    except:
        last_seen = models.LastSeen.objects.create(user=user, room=chatroom, date=date)
    return Response({"success": True})

# endregion


# region > Course

COURSES_PER_PAGE = 10
DEFAULT_RADIUS = 10000

@api_view(['GET'])
def getCourses(request):
    trainer_id = request.GET.get('trainer')
    sport = request.GET.get('sport')
    latlng = request.GET.get('latlng')
    radius = request.GET.get('radius')

    if trainer_id:
        courses = models.Course.objects.filter(trainer_id=trainer_id)
    else:
        courses = models.Course.objects.all()
    
    if sport:
        courses = courses.filter(sport=sport)

    if latlng:
        lat, lng = (float(i) for i in latlng.split(','))
        radius = float(radius) if radius is not None else DEFAULT_RADIUS
        print("========= lat, lng, radius", lat, lng, radius)
        
        # Lọc các khóa học có location và tính khoảng cách
        courses = courses.exclude(location=None)
        
        # Sử dụng raw SQL để tính khoảng cách với Haversine formula
        courses = courses.extra(
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
            params=[lat, lng, lat, radius/1000], # Chuyển đổi radius từ mét sang km
            tables=['base_location']
        ).filter(location__id__isnull=False)
        print("========= courses", courses.count())
        
        # Sắp xếp theo khoảng cách
        courses = courses.order_by('distance')

    page = request.GET.get('page')
    if page:
        page = int(page)
        if page > courses.count() // COURSES_PER_PAGE:
            return Response({"success": False, "message": "Page out of range"}, status=400)
        courses = courses.order_by('-id')[page*COURSES_PER_PAGE:(page+1)*COURSES_PER_PAGE]

    serializer = srl.CourseSerializer(courses, many=True, context={'request': request})
    response = serializer.data

    return Response(status=200, data=response)


@api_view(['GET'])
def getCourse(request, pk):
    serializer = srl.CourseSerializer(
        models.Course.objects.get(id=pk), 
        many=False, 
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['POST'])
def createCourse(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"}, status=400)

    user = request.user
    if not user.isTrainer:
        return Response({"success": False, "message": f"You're not a trainer"}, status=400)

    data = convert_data_type(request.data)
    location = data.pop("location", None)
    form = forms.CourseForm(data)
    if form.is_valid():
        try:
            course = form.save(commit=False)
            course.trainer = user
            
            if 'image' in request.FILES:
                image = request.FILES['image']
                # Lưu ảnh vào một thư mục trên server
                file_path = os.path.join(settings.MEDIA_ROOT, image.name)
                with open(file_path, 'wb+') as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                course.image = image.name
            course.save()

            # add location
            # location = data["location"]
            if location is not None:
                location_form = forms.LocationForm(location)
                if not location_form.is_valid():
                    return Response({"success": False, "message": get_form_errors(location_form)}, status=400)
                location = location_form.save(commit=False)
                location.course = course
                location.save()

            serializer = srl.CourseSerializer(course, many=False, context={'request': request})
            return Response({"success": True, "course": serializer.data})
            # return Response({"success": True})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=400)
    else:
        return Response({"success": False, "message": get_form_errors(form)}, status=400)
    

@api_view(['POST'])
def updateCourse(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"})

    user = request.user
    
    data = convert_data_type(request.data)
    location = data.pop("location", None)
    print("================ data", data)
    print("================ location", location)
    course = user.courses.get(id=data["id"])
    form = forms.CourseForm(data, instance=course)
    if form.is_valid():
        try:
            if 'image' in request.FILES:
                image = request.FILES['image']
                # Lưu ảnh vào một thư mục trên server
                file_path = os.path.join(settings.MEDIA_ROOT, image.name)
                with open(file_path, 'wb+') as f:
                    for chunk in image.chunks():
                        f.write(chunk)
                course.image = image.name

            course.save()
            form.save()

            # add location
            # location = data["location"]
            if location is not None:
                if hasattr(course, 'location') and course.location:
                    course.location.delete()
                location_form = forms.LocationForm(location)
                if not location_form.is_valid():
                    return Response({"success": False, "message": get_form_errors(location_form)}, status=400)
                location = location_form.save(commit=False)
                location.course = course
                location.save()

            serializer = srl.CourseSerializer(course, many=False, context={'request': request})
            return Response({"success": True, "course": serializer.data})
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=400)
    
    else:
        return Response({"success": False, "message": get_form_errors(form)}, status=400)
    

@api_view(['GET'])
def deleteCourse(request, pk):
    user = request.user
    try:
        user.courses.get(id=pk).delete()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=400)

# endregion


SESSIONS_PER_PAGE = 10


# region > Training Session

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
            update_sessions = locked_training_sessions.filter(start__gte=start, 
                                                              end__lte=end)
            for update_session in update_sessions:
                if update_session.booking_sessions.count() > 0:
                    return None
            update_sessions.delete()
        except: 
            pass

        try:
            update_session = locked_training_sessions.get(start__lt=start, 
                                                            end__gt=end)
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
            update_session = locked_training_sessions.get(start__lt=start, 
                                                            end__gt=start)
            if update_session.booking_sessions.count() > 0:
                return None
            update_session.end = training_session.start
            update_session.save()
        except: 
            pass

        try:
            update_session = locked_training_sessions.get(start__lt=end, 
                                                            end__gt=end)
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

    # Khóa course và các training sessions liên quan với timeout 3 giây
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


def try_to_add_training_sessions(booking_sessions, timeout=30) -> dict:
    booking_to_locked_training_sessions = {}
    with transaction.atomic():
        booking_to_locked_training_sessions = get_booking_to_locked_training_sessions(booking_sessions, timeout)
        
        if not check_booking_sesssions(booking_sessions):
            raise Exception("Booking sessions are not valid")

        booking_to_training_sessions = {}
        for booking_session, locked_training_sessions in booking_to_locked_training_sessions.items():
            training_session = add_training_session(booking_session, locked_training_sessions)
            if training_session is None:
                raise Exception("Can't add training session")
            booking_to_training_sessions[booking_session] = training_session

        return booking_to_training_sessions


@api_view(['GET'])
def getTrainingSessions(request):
    user = request.user
    course_id = request.GET.get('course_id')
    from_date = request.GET.get('from') 
    to_date = request.GET.get('to')
    page = request.GET.get('page')
    booked = request.GET.get('booked')
    reverse = request.GET.get('reverse')
    
    if course_id:
        training_sessions = models.TrainingSession.objects.filter(course_id=course_id)
    elif user.isTrainer:
        training_sessions = models.TrainingSession.objects.filter(course__trainer=user)
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

    serializer = srl.TrainingSessionSerializer(training_sessions, 
                                               context={'request': request}, 
                                               many=True)
    response = serializer.data
    return Response(response)


@api_view(['GET'])
def getTrainingSession(request, pk):
    user = request.user
    if user.isTrainer:
        training_session = models.TrainingSession.objects.get(id=pk)
        if training_session.course.trainer != user:
            return Response({"success": False, 
                             "message": "You're not the trainer of this course"}, 
                             status=400)
    else:
        booking_session = models.BookingSession.objects.get(id=pk)
        if booking_session.user != user:
            return Response({"success": False, 
                             "message": "You're not the user of this booking session"}, 
                             status=400)
        
        training_session = booking_session.training_session

    serializer = srl.TrainingSessionDetailSerializer(
        training_session, 
        many=False, 
        context={'request': request}
    )
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
            course = user.courses.get(id=request.data["course"])
            training_session = form.save(commit=False)

            try:
                update_sessions = course.training_sessions.filter(start__gte=training_session.start, 
                                                                end__lte=training_session.end)
                for update_session in update_sessions:
                    if update_session.booking_sessions.count() > 0:
                        return Response({"success": False, "message": "Schedule conflict"}, status=400)
                update_sessions.delete()
            except: 
                pass

            try:
                update_session = course.training_sessions.get(start__lt=training_session.start, 
                                                                end__gt=training_session.end)
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
                update_session = course.training_sessions.get(start__lt=training_session.start, 
                                                                end__gt=training_session.start)
                if update_session.booking_sessions.count() > 0:
                    return Response({"success": False, "message": "Schedule conflict"}, status=400)
                update_session.end = training_session.start
                update_session.save()
            except: 
                pass

            try:
                update_session = course.training_sessions.get(start__lt=training_session.end, 
                                                                end__gt=training_session.end)
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

def check_booking_sesssions(booking_sessions):
    # Reorder sessions by start time
    booking_sessions = list(booking_sessions)
    booking_sessions.sort(key=lambda x: x.start)
    
    # Checking if all the sessions are valid
    for i, booking_session in enumerate(booking_sessions):
        course = booking_session.course
        if i > 0 and booking_session.start < booking_sessions[i-1].end:
            return False
        
        try:
            training_session = course.training_sessions.get(start__lte=booking_session.start, 
                                                            end__gte=booking_session.end)
            # Kiểm tra số lượng học viên trong mỗi session
            if training_session.booking_sessions.count() >= course.max_trainee:
                return False
        except Exception as e:
            print("======================== error:", e)
            return False
        
    return True


def add_booking_session(user, payment_history, training_session):
    form = forms.BookingSessionForm({
        "user": user.id, 
        "payment_history": payment_history.id, 
        "training_session": training_session.id
    })
    if form.is_valid():
        booking_session = form.save(commit=False)
        booking_session.user = user
        booking_session.save()
        return booking_session
    
    return None


@api_view(['GET'])
def getBookingSessions(request):
    user = request.user
    from_date = request.GET.get('from') 
    to_date = request.GET.get('to')
    page = request.GET.get('page')
    reverse = request.GET.get('reverse')

    # Lọc các booking session có training_session khác None
    booking_sessions = user.booking_sessions.all()
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


    serializer = srl.BookingSessionSerializer(
        booking_sessions, 
        many=True, 
        context={'request': request}
    )
    return Response(serializer.data)


@api_view(['GET'])
def getBookingSession(request, pk):
    user = request.user
    serializer = srl.BookingSessionSerializer(
        user.booking_sessions.get(id=pk), 
        many=False, 
        context={'request': request}
    )
    return Response(serializer.data)


@login_required(login_url='api-login')
@api_view(['POST'])
def addBookingSession(request):
    if request.method != 'POST':
        return Response({"success": False, "message": f"Wrong method, expect: POST"}, status=400)

    user = request.user

    form = forms.BookingSessionForm(request.data)
    if form.is_valid():
        training_session = models.TrainingSession.objects.get(id=request.data["training_session"])
        ntrainees = training_session.booking_sessions.count()
        if ntrainees >= training_session.course.max_trainee:
            return Response({"success": False, "message": "Training Session is full"}, status=400)

        booking_session = form.save(commit=False)
        booking_session.user = user
        booking_session.save()
        return Response({"success": True}, status=200)
    else:
        return Response({"success": False, "message": get_form_errors(form)}, status=400)


@login_required(login_url='api-login')
@api_view(['GET'])
def deleteBookingSession(request, pk):
    user = request.user
    try:
        user.booking_sessions.get(id=pk).delete()
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
        return Response({"success": False, "message": get_form_errors(form)}, status=400)
    

@api_view(['GET'])
def getRatings(request, course_pk):
    rating = models.Course.objects.get(id=course_pk).ratings
    serializer = srl.RatingSerializer(rating, many=True)
    return Response(serializer.data)

# endregion
