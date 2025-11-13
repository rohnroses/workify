from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile, Order, OrderApplication, Category, ROLE_CHOICES
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

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('status',)

class OrderApplicationSerializerForEmployer(serializers.ModelSerializer):
    class Meta:
        model = OrderApplication
        fields = ['order', 'worker', 'cover_letter', 'status', 'created_at']
        read_only_fields = ('status',)

        


class OrderApplicationSerializer(serializers.ModelSerializer):
    worker = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = OrderApplication
        fields = ['id', 'order', 'worker', 'cover_letter', 'status', 'created_at']
        read_only_fields = ('status',)

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = '__all__'

