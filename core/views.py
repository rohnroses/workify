from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions, generics
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password, ValidationError
from django.db import IntegrityError
from django.template.context_processors import request
from .serializers import RegisterSerializer
from .models import Order, OrderApplication, Profile, Category, Review
from .serializers import OrderSerializer, CategorySerializer, ProfileSerializer, OrderApplicationSerializer, OrderApplicationSerializerForEmployer, ReviewSerializer
from .permissions import IsEmployer, IsWorker
from .services import (
    UserService, OrderService, OrderApplicationService, 
    ReviewService, ProfileService, CategoryService
)

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
    serializer_class = OrderSerializer
    
    def get_queryset(self):
        category = self.request.query_params.get('category')
        return OrderService.get_orders_by_category(category)
    
class MyOrdersAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return OrderService.get_user_orders(self.request.user)
        

class CreateOrderAPIView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsEmployer]
    
    def perform_create(self, serializer):
        OrderService.create_order(serializer.validated_data)


class DeleteOrderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def delete(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
            OrderService.delete_order(order, request.user)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Order.DoesNotExist:
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CategoryAPIView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]   

    def get_object(self):
        return ProfileService.get_user_profile(self.request.user)

class CreateOrderApplicationAPIView(generics.CreateAPIView):
    serializer_class = OrderApplicationSerializer
    permission_classes = [IsWorker]

class ApplicationAPIView(generics.ListAPIView):
    serializer_class = OrderApplicationSerializerForEmployer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get_queryset(self):
        order_id = self.request.query_params.get('order')
        return OrderApplicationService.get_employer_applications(self.request.user, order_id)

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
        
        try:
            if action == 'accept':
                application, order = OrderApplicationService.accept_application(
                    application, request.user
                )
                return Response({
                    'message': 'Application accepted and order status updated to in progress',
                    'application': OrderApplicationSerializerForEmployer(application).data,
                    'order': OrderSerializer(order).data
                })
            
            elif action == 'reject':
                application = OrderApplicationService.reject_application(
                    application, request.user
                )
                return Response({
                    'message': 'Application rejected',
                    'application': OrderApplicationSerializerForEmployer(application).data
                })
            
            else:
                return Response(
                    {'detail': 'Invalid action. Use "accept" or "reject"'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class ApplicationListByOrderAPIView(generics.ListAPIView):
    serializer_class = OrderApplicationSerializerForEmployer
    permission_classes = [permissions.IsAuthenticated, IsEmployer]

    def get_queryset(self):
        order_id = self.kwargs.get('order_id')
        return OrderApplicationService.get_applications_by_order(order_id, self.request.user)

class CreateReviewAPIView(generics.CreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsEmployer]

    def perform_create(self, serializer):
        ReviewService.create_review(serializer.validated_data, self.request.user)

class WorkerApplicationsAPIView(generics.ListAPIView):
    serializer_class = OrderApplicationSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorker]

    def get_queryset(self):
        return OrderApplicationService.get_worker_applications(self.request.user)

class ReviewAPIView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        order_id = self.request.query_params.get('order')
        worker_id = self.request.query_params.get('user')
        return ReviewService.get_user_reviews(self.request.user, order_id, worker_id)


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
        
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'detail': 'Status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = OrderService.update_order_status(order, new_status, request.user)
            return Response({
                'message': f'Order status updated to {new_status}',
                'order': OrderSerializer(order).data
            }, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response(
                {'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class WorkerAcceptedOrdersAPIView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsWorker]

    def get_queryset(self):
        return OrderService.get_worker_accepted_orders(self.request.user)


class JobStatsAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'total_jobs': OrderService.get_total_job_count(),
            'total_categories': Category.objects.count()
        })


class CategorySyncAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request):
        CategoryService.sync_category_job_counts()
        return Response({'message': 'Category job counts synced successfully'})

# ВРЕМЕННЫЙ ЭНДПОИНТ ДЛЯ НАПОЛНЕНИЯ
class BulkCategoryCreateView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        names = request.data.get('names', [])
        created_count = 0
        for name in names:
            Category.objects.get_or_create(name=name)
            created_count += 1
        return Response({"message": f"Successfully created {created_count} categories"})