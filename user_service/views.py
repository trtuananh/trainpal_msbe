from django.contrib.auth import login, logout, authenticate
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
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

@api_view(['POST'])
def login_user(request):
    if request.method != 'POST':
        return Response({"success": False, "message": "Wrong method, expect: POST"}, status=400)

    data = request.data
    username = data["username"]
    password = data["password"]

    if not models.User.objects.filter(username=username).exists():
        try:
            username = models.User.objects.get(email=username).username
        except:
            return Response({"success": False, "message": "Invalid username"}, status=401)

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
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
        return Response({"success": False, "message": "Wrong password!"}, status=401)

@api_view(['GET'])
def logout_user(request):
    logout(request)
    return Response({"success": True})

@api_view(['POST'])
def register_user(request):
    if request.method != 'POST':
        return Response({"success": False, "message": "Wrong method, expect: POST"}, status=400)

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
        return Response({"success": False, "message": get_form_errors(form)}, status=400)

class TokenRefreshView(APIView):
    def post(self, request):
        refresh_token = request.data.get('refresh')
        try:
            if not refresh_token:
                return Response({"success": False, "message": "Refresh token is required"}, status=400)
            
            refresh = RefreshToken(refresh_token)
            access = str(refresh.access_token)
            return Response({
                'access': access,
                'refresh': refresh_token
            })
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
def user_profile(request, pk):
    user = models.User.objects.get(id=pk)
    serializer = serializers.UserSerializer(user, many=False, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
def update_profile(request):
    user = request.user
    data = convert_data_type(request.data)
    if user.id != data["id"]:
        return Response({"success": False, "message": "You are not allowed to update this profile"}, status=400)

    if request.method != 'POST':
        return Response({"success": False, "message": "Wrong method, expect: POST"}, status=400)

    try:
        form = forms.UserForm(data, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return Response(serializers.UserSerializer(user, many=False, context={'request': request}).data)
        else:
            return Response({"success": False, "message": get_form_errors(form)}, status=400)
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=400)
