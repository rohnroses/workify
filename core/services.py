from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError
from .models import Order, OrderApplication, Profile, Review, Category


class UserService:
    @staticmethod
    def create_user(validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class OrderService:
    @staticmethod
    def get_orders_by_category(category=None):
        queryset = Order.objects.all().select_related('employer', 'category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    @staticmethod
    def get_user_orders(user):
        return Order.objects.filter(employer=user).select_related('employer', 'category')
    
    @staticmethod
    @transaction.atomic
    def create_order(validated_data):
        order = Order.objects.create(**validated_data)
        Category.objects.filter(id=order.category.id).update(job_count=F('job_count') + 1)
        return order
    
    @staticmethod
    @transaction.atomic
    def delete_order(order, user):
        if order.employer != user:
            raise ValidationError('You do not have permission to delete this order')
        
        category_id = order.category.id
        order.delete()
        Category.objects.filter(id=category_id).update(job_count=F('job_count') - 1)

    @staticmethod
    def update_order_status(order, new_status, user):
        if order.employer != user:
            raise ValidationError('You do not have permission to manage this order')
        
        valid_statuses = ['open', 'in_progress', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            raise ValidationError(f'Invalid status. Must be one of: {", ".join(valid_statuses)}')
        
        valid_transitions = {
            'open': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled'],
            'completed': [],
            'cancelled': []
        }
        
        if new_status not in valid_transitions.get(order.status, []):
            raise ValidationError(
                f'Cannot transition from "{order.status}" to "{new_status}". '
                f'Valid transitions: {valid_transitions.get(order.status, [])}'
            )
        
        order.status = new_status
        order.save()
        return order
    
    @staticmethod
    def get_worker_accepted_orders(user):
        return Order.objects.filter(
            applications__worker=user,
            applications__status='accepted'
        ).distinct().select_related('employer', 'category')

    @staticmethod
    def get_total_job_count():
        return Order.objects.filter(status='open').count()


class CategoryService:
    @staticmethod
    def get_all_categories():
        return Category.objects.all()

    @staticmethod
    @transaction.atomic
    def sync_category_job_counts():
        categories = Category.objects.all()
        for category in categories:
            count = Order.objects.filter(category=category, status='open').count()
            Category.objects.filter(id=category.id).update(job_count=count)
        return Category.objects.all()


class OrderApplicationService:
    @staticmethod
    def get_employer_applications(user, order_id=None):
        queryset = OrderApplication.objects.filter(
            order__employer=user
        ).select_related('order', 'worker').prefetch_related('order__category')
        
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        
        return queryset
    
    @staticmethod
    def get_applications_by_order(order_id, user):
        return OrderApplication.objects.filter(
            order_id=order_id,
            order__employer=user
        ).select_related('order', 'worker').prefetch_related('order__category')
    
    @staticmethod
    def get_worker_applications(user):
        return OrderApplication.objects.filter(
            worker=user
        ).select_related('order', 'order__employer').prefetch_related('order__category')
    
    @staticmethod
    @transaction.atomic
    def accept_application(application, user):
        order = application.order
        
        if order.employer != user:
            raise ValidationError('You do not have permission to manage this application')
        
        if order.status != 'open':
            raise ValidationError('This order is no longer open for applications')
        
        order.status = 'in_progress'
        order.save()
        
        application.status = 'accepted'
        application.save()
        
        OrderApplication.objects.filter(order=order).exclude(pk=application.pk).update(status='rejected')
        
        return application, order
    
    @staticmethod
    def reject_application(application, user):
        order = application.order
        
        if order.employer != user:
            raise ValidationError('You do not have permission to manage this application')
        
        if application.status != 'pending':
            raise ValidationError('Can only reject pending applications')
        
        application.status = 'rejected'
        application.save()
        
        return application
    
    @staticmethod
    def create_application(validated_data):
        return OrderApplication.objects.create(**validated_data)


class ReviewService:
    @staticmethod
    def create_review(validated_data, reviewer):
        order = validated_data['order']
        
        try:
            accepted_app = OrderApplication.objects.get(order=order, status='accepted')
            worker = accepted_app.worker
        except OrderApplication.DoesNotExist:
            raise ValidationError(
                "No accepted worker found for this order. Ensure you have accepted an application."
            )
        
        validated_data['reviewer'] = reviewer
        validated_data['worker'] = worker
        
        return Review.objects.create(**validated_data)
    
    @staticmethod
    def get_user_reviews(user, order_id=None, worker_id=None):
        queryset = Review.objects.all().select_related(
            'order', 'order__employer', 'reviewer', 'worker'
        ).prefetch_related('order__category')
        
        if user.profile.role == 'employer':
            queryset = queryset.filter(order__employer=user)
        else:
            queryset = queryset.filter(worker=user)
        
        if order_id:
            queryset = queryset.filter(order_id=order_id)
        if worker_id:
            queryset = queryset.filter(worker_id=worker_id)
        
        return queryset


class ProfileService:
    @staticmethod
    def get_user_profile(user):
        return Profile.objects.get(user=user)
    
    @staticmethod
    def update_user_profile(user, validated_data):
        profile = Profile.objects.get(user=user)
        for attr, value in validated_data.items():
            setattr(profile, attr, value)
        profile.save()
        return profile
