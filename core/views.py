from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password, ValidationError
from django.db import IntegrityError
from django.template.context_processors import request
from .serializers import RegisterSerializer
from .models import Order, OrderApplication, Profile, Category
from .serializers import OrderSerializer, CategorySerializer, ProfileSerializer, OrderApplicationSerializer, OrderApplicationSerializerForEmployer
from .permissions import IsEmployer, IsWorker

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "Пользователь успешно создан!",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                },
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrderAPIView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        queryset = queryset.filter(employer=self.request.user)
        return queryset
    
class MyOrdersAPIView(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(employer=self.request.user)
        return queryset
        

class CreateOrderAPIView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsEmployer]

class CategoryAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]   

    def get_object(self):
        return Profile.objects.get(user=self.request.user)

class CreateOrderApplicationAPIView(generics.CreateAPIView):
    serializer_class = OrderApplicationSerializer
    permission_classes = [IsWorker]

class ApplicationAPIView(generics.ListAPIView):
    queryset = OrderApplication.objects.all()
    serializer_class = OrderApplicationSerializerForEmployer
    permission_classes = [IsEmployer]


    def get_queryset(self):
        order_id = self.request.query_params.get('order')
        queryset = super().get_queryset()
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        queryset = queryset.filter(order__employer=self.request.user)
        return queryset