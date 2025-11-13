from django.urls import path 
from .views import RegisterView, OrderAPIView, CreateOrderAPIView, CategoryAPIView, ProfileAPIView, CreateOrderApplicationAPIView, MyOrdersAPIView, ApplicationAPIView

urlpatterns = [
    path('api/v1/register/', RegisterView.as_view(), name='register'),
    path('api/v1/orderlist/', OrderAPIView.as_view(), name='orderlist'),
    path('api/v1/ordercreate/', CreateOrderAPIView.as_view(), name='create-order'),
    path('api/v1/categorylist/', CategoryAPIView.as_view(), name='categorylist'),
    path('api/v1/profile/', ProfileAPIView.as_view(), name='profile'),
    path('api/v1/profile/<int:pk>/', ProfileAPIView.as_view(), name ='update-profile'),
    path('api/v1/applicationcreate/', CreateOrderApplicationAPIView.as_view(), name='create-application'),  
    path('api/v1/myorderslist/', MyOrdersAPIView.as_view(), name='myorderslist'),
    path('api/v1/applicationlist/', ApplicationAPIView.as_view(), name='applicationlist'),
]

