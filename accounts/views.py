from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth.decorators import login_required
from .serializers import RegisterSerializer, LoginSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# Create your views here.

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                # Create a Django session so @login_required-protected pages work.
                django_login(request, user)
                return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
            return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# note to self: this is a protected view that requires authentication. If the user is not authenticated, they will be redirected to the login page.
#we use @login_required so only authenticated users can access the dashboard page.
@login_required(login_url='/accounts/login-page/')
def dashboard_page(request):
    return render(request, 'dashboard.html')


@login_required(login_url='/accounts/login-page/')
def user_page(request):
    return render(request, 'user.html')





#frontend code for login and registration
def register_page(request):
    return render(request, 'register.html')

def login_page(request):
    return render(request, 'login.html')



