import uuid
import hmac
import hashlib
import json
import requests
from django.utils import timezone
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from dateutil import parser
from . import models
from . import serializers
from course_service.views import check_booking_sessions, try_to_add_training_sessions

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
def get_payments(request):
    user = request.user
    page = request.GET.get('page')
    now = timezone.now()
    PAYMENT_PER_PAGE = 20
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    is_trainer = check_user_is_trainer(user.id, access_token)

    if is_trainer:
        payments = models.Payment.objects.filter(receiver_id=user.id).exclude(
            payment_method='OFF',
            booking_sessions__end__gte=now
        )
    else:
        payments = models.Payment.objects.filter(sender_id=user.id).exclude(
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

    serializer = serializers.PaymentSerializer(payments, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
def get_payment(request, pk):
    user = request.user
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    is_trainer = check_user_is_trainer(user.id, access_token)
    payment = models.Payment.objects.get(id=pk)

    if is_trainer:
        if payment.receiver_id != user.id:
            return Response({"success": False, "message": "You are not the receiver of this payment"}, status=400)
    else:
        if payment.sender_id != user.id:
            return Response({"success": False, "message": "You are not the sender of this payment"}, status=400)

    serializer = serializers.PaymentSerializer(payment, many=False, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def create_payment(request):
    user = request.user
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    try:
        # Fetch course from course_service
        course_response = requests.get(
            f"http://localhost:8000/api/course/course/{request.data['course']}/",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        if course_response.status_code != 200:
            return Response({"success": False, "message": "Course not found"}, status=400)
        course_data = course_response.json()

        sessions = request.data["sessions"]
        payment_method = request.data["payment_method"]
        order_info = request.data.get("order_info")
        redirect_url = request.data.get("redirect_url")
        ipn_url = request.data.get("ipn_url")
        lang = request.data.get("lang")
        total_price = 0
        booking_sessions = []

        # Create booking sessions in course_service
        for session in sessions:
            start = parser.isoparse(session["start"])
            end = parser.isoparse(session["end"])
            price = course_data['unit_price'] * (end - start).total_seconds() / (3600 * course_data['unit_session'])
            total_price += price
            booking_response = requests.post(
                "http://localhost:8000/api/course/add-booking/",
                json={
                    "user_id": user.id,
                    "course": course_data['id'],
                    "start": session["start"],
                    "end": session["end"],
                    "price": price,
                    "training_session": None
                },
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if booking_response.status_code != 200:
                for bs in booking_sessions:
                    requests.get(f"http://localhost:8000/api/course/delete-booking/{bs['id']}/", headers={'Authorization': f'Bearer {access_token}'})
                return Response({"success": False, "message": booking_response.json().get("message", "Failed to create booking session")}, status=400)
            booking_sessions.append(booking_response.json())

        # Validate booking sessions
        booking_session_objects = []
        for bs in booking_sessions:
            bs_response = requests.get(
                f"http://localhost:8000/api/course/booking/{bs['id']}/",
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if bs_response.status_code == 200:
                booking_session_objects.append(bs_response.json())
            else:
                for bs in booking_sessions:
                    requests.get(f"http://localhost:8000/api/course/delete-booking/{bs['id']}/", headers={'Authorization': f'Bearer {access_token}'})
                return Response({"success": False, "message": "Failed to fetch booking session"}, status=400)

        if not check_booking_sessions(booking_session_objects):
            for bs in booking_sessions:
                requests.get(f"http://localhost:8000/api/course/delete-booking/{bs['id']}/", headers={'Authorization': f'Bearer {access_token}'})
            return Response({"success": False, "message": "Sessions are not available"}, status=400)

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
                for bs in booking_sessions:
                    requests.get(f"http://localhost:8000/api/course/delete-booking/{bs['id']}/", headers={'Authorization': f'Bearer {access_token}'})
                return Response({"success": False, "message": momo_response.get("message")}, status=400)

            payment = models.Payment.objects.create(
                payment_id=payment_id,
                sender_id=user.id,
                receiver_id=course_data['trainer_id'],
                payment_method=payment_method,
                value=total_price,
                is_paid=False
            )

            # Update booking sessions with payment_id
            for bs in booking_sessions:
                requests.post(
                    f"http://localhost:8000/api/course/update-booking/{bs['id']}/",
                    json={"payment_id": payment.id},
                    headers={'Authorization': f'Bearer {access_token}'}
                )

            response = serializers.PaymentSerializer(payment, many=False, context={'request': request}).data
            response["payUrl"] = momo_response.get("payUrl") if momo_response else ""
            return Response(response)

        else:  # offline payment
            booking_to_training_sessions = try_to_add_training_sessions(booking_session_objects)
            payments = []
            for booking_session, training_session in booking_to_training_sessions.items():
                payment = models.Payment.objects.create(
                    payment_id=str(uuid.uuid4()),
                    sender_id=user.id,
                    receiver_id=course_data['trainer_id'],
                    payment_method=payment_method,
                    value=booking_session['price'],
                    is_paid=True,
                    success=True,
                )
                payments.append(payment)
                requests.post(
                    f"http://localhost:8000/api/course/update-booking/{booking_session['id']}/",
                    json={"payment_id": payment.id, "training_session": training_session['id']},
                    headers={'Authorization': f'Bearer {access_token}'}
                )

            response = serializers.PaymentSerializer(payments, many=True, context={'request': request}).data
            return Response(response)

    except Exception as e:
        for bs in booking_sessions:
            requests.get(f"http://localhost:8000/api/course/delete-booking/{bs['id']}/", headers={'Authorization': f'Bearer {access_token}'})
        if 'payment' in locals():
            payment.delete()
        elif 'payments' in locals():
            for payment in payments:
                payment.delete()
        return Response({"success": False, "message": str(e)}, status=400)

@api_view(['POST'])
def momo_payment_callback(request):
    access_token = request.headers.get('Authorization', '').split('Bearer ')[-1]
    data = request.data
    accessKey = MomoAPI.accessKey
    amount = data.get('amount')
    extraData = data.get('extraData')
    message = data.get('message')
    orderId = data.get('orderId')
    orderInfo = data.get('orderInfo')
    orderType = data.get('orderType')
    partnerCode = MomoAPI.partnerCode
    payType = data.get('payType')
    requestId = data.get('requestId')
    responseTime = data.get('responseTime')
    resultCode = data.get('resultCode')
    transId = data.get('transId')

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

    signature = data.get('signature')
    if signature != expectedSignature:
        return Response({"success": False, "message": "Signature không khớp"}, status=400)

    try:
        payment = models.Payment.objects.get(payment_id=orderId)
        if payment.is_paid:
            response = serializers.PaymentSerializer(payment, many=False, context={'request': request}).data
            return Response(response)

        if int(resultCode) == 0:
            payment.is_paid = True
            payment.momo_transaction_id = transId
            payment.momo_payment_type = payType

            # Fetch and update booking sessions
            booking_sessions_response = requests.get(
                f"http://localhost:8000/api/course/booking-by-payment/{payment.id}/",
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if booking_sessions_response.status_code != 200:
                payment.success = False
                payment.message = "Failed to fetch booking sessions"
                payment.save()
                return Response({"success": False, "message": "Failed to fetch booking sessions"}, status=400)

            booking_sessions = booking_sessions_response.json()
            booking_to_training_sessions = try_to_add_training_sessions(booking_sessions)

            for booking_session, training_session in booking_to_training_sessions.items():
                requests.post(
                    f"http://localhost:8000/api/course/update-booking/{booking_session['id']}/",
                    json={"training_session": training_session['id']},
                    headers={'Authorization': f'Bearer {access_token}'}
                )

            payment.success = True
        else:
            payment.message = message

        payment.save()
        response = serializers.PaymentSerializer(payment, many=False, context={'request': request}).data
        return Response(response)

    except Exception as e:
        if 'payment' in locals():
            payment.success = False
            payment.message = "Sessions are not available"
            payment.save()
        return Response({"success": False, "message": str(e)}, status=400)

@api_view(['GET'])
def momo_payment(request):
    amount = "50000"
    payment_id = str(uuid.uuid4())
    order_info = "pay with MoMo"
    response = MomoAPI.create_payment(amount, payment_id)
    return Response(response)

@api_view(['POST'])
def verify_momo_payment(request):
    payment_id = request.data.get('orderId')
    response = MomoAPI.verify_payment(payment_id)
    return Response(response)

class MomoAPI:
    accessKey = "F8BBA842ECF85"
    secretKey = "K951B6PE1waDMi640xX08PD3vg6EkVlz"
    orderInfo = "pay with MoMo"
    partnerCode = "MOMO"
    redirectUrl = "trainpal://home"
    ipnUrl = "https://trainpal.vn/api/payment/momo-payment-callback/"
    extraData = ""
    partnerName = "TrainPal"
    requestType = "payWithMethod"
    storeId = "Test Store"
    orderGroupId = ""
    autoCapture = True
    lang = "vi"

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
            requestType=requestType
        )

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
            requestId=requestId
        )

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
    