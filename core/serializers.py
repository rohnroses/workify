from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Order, OrderApplication, Category, ROLE_CHOICES, Review
from django.contrib.auth.password_validation import validate_password


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=ROLE_CHOICES, default='worker')

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs
    
    def create(self, validated_data):
        role = validated_data.pop('role', 'worker')
        validated_data.pop('password2')  
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user, role=role)
        return user
    
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    employer = serializers.HiddenField(default=serializers.CurrentUserDefault())
    category_name = serializers.CharField(source='category.name', read_only=True)
    employer_username = serializers.CharField(source='employer.username', read_only=True)
    

    class Meta:
        model = Order
        fields = ['id', 'employer', 'employer_username', 'title', 'description', 'budget', 'category', 'category_name', 'status', 'created_at']
        read_only_fields = ('status', 'created_at')


class OrderApplicationSerializerForEmployer(serializers.ModelSerializer):
    worker_username = serializers.CharField(source='worker.username', read_only=True)
    worker_email = serializers.CharField(source='worker.email', read_only=True)
    order_title = serializers.CharField(source='order.title', read_only=True)
    
    class Meta:
        model = OrderApplication
        fields = ['id', 'order', 'order_title', 'worker', 'worker_username', 'worker_email', 'cover_letter', 'status', 'created_at']
        read_only_fields = ('status', 'created_at')


class OrderApplicationSerializer(serializers.ModelSerializer):
    worker = serializers.HiddenField(default=serializers.CurrentUserDefault())
    order_title = serializers.CharField(source='order.title', read_only=True)
    order_budget = serializers.CharField(source='order.budget', read_only=True)
    employer_username = serializers.CharField(source='order.employer.username', read_only=True)
    
    class Meta:
        model = OrderApplication
        fields = ['id', 'order', 'order_title', 'order_budget', 'employer_username', 'worker', 'cover_letter', 'status', 'created_at']
        read_only_fields = ('status', 'created_at')

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    reviewer_username = serializers.CharField(source='reviewer.username', read_only=True)
    worker_username = serializers.CharField(source='worker.username', read_only=True)
    order_title = serializers.CharField(source='order.title', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'order', 'order_title', 'reviewer', 'reviewer_username', 'worker', 'worker_username', 'rating', 'comment', 'created_at']
        read_only_fields = ('created_at', 'reviewer', 'worker')

    def validate(self, attrs):
        order = attrs.get('order')
        request = self.context.get('request')
        
        if not order:
            raise serializers.ValidationError({'order': 'Order is required'})
        
        if order.status != 'completed':
            raise serializers.ValidationError({'order': 'Order must be completed before leaving a review'})
        
        if not request or order.employer != request.user:
            raise serializers.ValidationError({'order__employer': 'You can only review your own orders'})
        
        if Review.objects.filter(order=order).exists():
            raise serializers.ValidationError({'order': 'This order already has a review.'})
        
        rating = attrs.get('rating')
        if not rating or not (1 <= rating <= 5):
            raise serializers.ValidationError({'rating': 'Rating must be between 1 and 5.'})
        
        return attrs
