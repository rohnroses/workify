from django.contrib import admin
from .models import Profile, Category, Order, OrderApplication

admin.site.register(Profile)
admin.site.register(Order)
admin.site.register(Category)
admin.site.register(OrderApplication)