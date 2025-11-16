from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password, ValidationError
from django.db import IntegrityError
from django.template.context_processors import request
from .serializers import RegisterSerializer
from .models import Order, OrderApplication, Profile, Category, Review
from .serializers import OrderSerializer, CategorySerializer, ProfileSerializer, OrderApplicationSerializer, OrderApplicationSerializerForEmployer, ReviewSerializer
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
    serializer_class = OrderApplicationSerializerForEmployer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get_queryset(self):
        order_id = self.request.query_params.get('order')
        queryset = OrderApplication.objects.filter(order__employer=self.request.user).select_related('order', 'worker')
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        return queryset

    def post(self, request, *args, **kwargs):
        action = request.data.get('action')
        app_id = request.data.get('application_id')
        
        if not app_id or not action:
            return Response(
                {'detail': 'Missing application_id or action'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            application = OrderApplication.objects.get(id=app_id)
        except OrderApplication.DoesNotExist:
            return Response(
                {'detail': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        order = application.order
        
        if order.employer != request.user:
            return Response(
                {'detail': 'You do not have permission to manage this application'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if action == 'accept':
            if order.status != 'open':
                return Response(
                    {'detail': 'This order is no longer open for applications'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.status = 'in_progress'
            order.save()

            application.status = 'accepted'
            application.save()

            OrderApplication.objects.filter(order=order).exclude(pk=application.pk).update(status='rejected')

            return Response({
                'message': 'Application accepted and order status updated to in progress',
                'application': OrderApplicationSerializerForEmployer(application).data,
                'order': OrderSerializer(order).data
            })
        
        elif action == 'reject':
            if application.status != 'pending':
                return Response(
                    {'detail': 'Can only reject pending applications'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            application.status = 'rejected'
            application.save()
            
            return Response({
                'message': 'Application rejected',
                'application': OrderApplicationSerializerForEmployer(application).data
            })
        
        else:
            return Response(
                {'detail': 'Invalid action. Use "accept" or "reject"'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ApplicationListByOrderAPIView(generics.ListAPIView):
    serializer_class = OrderApplicationSerializerForEmployer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        queryset = OrderApplication.objects.filter(
            order_id=order_id,
            order__employer=self.request.user
        ).select_related('order', 'worker')
        return queryset

class CreateReviewAPIView(generics.CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsEmployer]

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)

class WorkerApplicationsAPIView(generics.ListAPIView):
    serializer_class = OrderApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorker]

    def get_queryset(self):
        return OrderApplication.objects.filter(worker=self.request.user).select_related('order', 'order__employer')

class ReviewAPIView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        order_id = self.request.query_params.get('order')
        worker_id = self.request.query_params.get('user')
        queryset = Review.objects.all().select_related('order', 'reviewer', 'worker')
        
        # Employers see reviews for their orders
        if self.request.user.profile.role == 'employer':
            queryset = queryset.filter(order__employer=self.request.user)
        # Workers see reviews about them
        else:
            queryset = queryset.filter(worker=self.request.user)
        
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        if worker_id:
            queryset = queryset.filter(worker_id=worker_id)
        return queryset


class UpdateOrderStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'detail': 'Order not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if order.employer != request.user:
            return Response(
                {'detail': 'You do not have permission to manage this order'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'detail': 'Status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_statuses = ['open', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return Response(
                {'detail': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_transitions = {
            'open': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': []
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            return Response(
                {'detail': f'Cannot transition from "{order.status}" to "{new_status}". Valid transitions: {valid_transitions.get(order.status, [])}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        return Response({
            'message': f'Order status updated to {new_status}',
            'order': OrderSerializer(order).data
        }, status=status.HTTP_200_OK)


class WorkerAcceptedOrdersAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorker]

    def get_queryset(self):
        return Order.objects.filter(
            applications__worker=self.request.user,
            applications__status='accepted'
        ).distinct().select_related('employer', 'category')