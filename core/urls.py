from django.urls import path 
from .views import (
    RegisterView, OrderAPIView, CreateOrderAPIView, CategoryAPIView, 
    ProfileAPIView, CreateOrderApplicationAPIView, MyOrdersAPIView, 
    ApplicationAPIView, ApplicationListByOrderAPIView, WorkerApplicationsAPIView, 
    ReviewAPIView, CreateReviewAPIView, UpdateOrderStatusAPIView, 
    WorkerAcceptedOrdersAPIView, JobStatsAPIView, CategorySyncAPIView,
    DeleteOrderAPIView
)

urlpatterns = [
    path('api/v1/register/', RegisterView.as_view(), name='register'),
    path('api/v1/orderlist/', OrderAPIView.as_view(), name='orderlist'),
    path('api/v1/ordercreate/', CreateOrderAPIView.as_view(), name='create-order'),
    path('api/v1/categorylist/', CategoryAPIView.as_view(), name='categorylist'),
    path('api/v1/profile/', ProfileAPIView.as_view(), name='profile'),
    path('api/v1/profile/<int:pk>/', ProfileAPIView.as_view(), name ='update-profile'),
    path('api/v1/applicationcreate/', CreateOrderApplicationAPIView.as_view(), name='create-application'),  
    path('api/v1/myorderslist/', MyOrdersAPIView.as_view(), name='myorderslist'),
    path('api/v1/myapplicationslist/', WorkerApplicationsAPIView.as_view(), name='myapplicationslist'),
    path('api/v1/myacceptedorders/', WorkerAcceptedOrdersAPIView.as_view(), name='myacceptedorders'),
    path('api/v1/applicationlist/', ApplicationAPIView.as_view(), name='applicationlist'),
    path('api/v1/orders/<int:order_id>/applications/', ApplicationListByOrderAPIView.as_view(), name='order-applications'),
    path('api/v1/orders/<int:order_id>/status/', UpdateOrderStatusAPIView.as_view(), name='update-order-status'),
    path('api/v1/reviewcreate/', CreateReviewAPIView.as_view(), name='create-review'),
    path('api/v1/reviewlist/', ReviewAPIView.as_view(), name='reviewlist'),
    path('api/v1/stats/', JobStatsAPIView.as_view(), name='job-stats'),
    path('api/v1/categories/sync/', CategorySyncAPIView.as_view(), name='categories-sync'),
    path('api/v1/orders/<int:pk>/delete/', DeleteOrderAPIView.as_view(), name='delete-order'),
]

