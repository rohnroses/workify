from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from decimal import Decimal
from .models import Profile, Category, Order, OrderApplication, Review
from .services import (
    UserService, OrderService, CategoryService, 
    OrderApplicationService, ReviewService, ProfileService
)


class UserServiceTestCase(TestCase):
    
    def test_create_user(self):
        user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        user = UserService.create_user(user_data)
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(User.objects.filter(username='testuser').exists())


class ProfileServiceTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = Profile.objects.create(
            user=self.user,
            role='employer',
            phone='+77001234567',
            bio='Test bio'
        )
    
    def test_get_user_profile(self):
        profile = ProfileService.get_user_profile(self.user)
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.role, 'employer')
    
    def test_update_user_profile(self):
        update_data = {
            'phone': '+77009999999',
            'bio': 'Updated bio',
            'city': 'almaty'
        }
        updated_profile = ProfileService.update_user_profile(self.user, update_data)
        
        self.assertEqual(updated_profile.phone, '+77009999999')
        self.assertEqual(updated_profile.bio, 'Updated bio')
        self.assertEqual(updated_profile.city, 'almaty')


class CategoryServiceTestCase(TestCase):
    
    def setUp(self):
        self.category1 = Category.objects.create(
            name='Programming',
            description='Programming jobs',
            job_count=0
        )
        self.category2 = Category.objects.create(
            name='Design',
            description='Design jobs',
            job_count=0
        )
        
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='pass123'
        )
        Profile.objects.create(user=self.employer, role='employer')
    
    def test_get_all_categories(self):
        categories = CategoryService.get_all_categories()
        self.assertEqual(categories.count(), 2)
    
    def test_sync_category_job_counts(self):
        Order.objects.create(
            employer=self.employer,
            title='Job 1',
            description='Description',
            budget=Decimal('1000.00'),
            category=self.category1,
            status='open'
        )
        Order.objects.create(
            employer=self.employer,
            title='Job 2',
            description='Description',
            budget=Decimal('2000.00'),
            category=self.category1,
            status='open'
        )
        Order.objects.create(
            employer=self.employer,
            title='Job 3',
            description='Description',
            budget=Decimal('1500.00'),
            category=self.category1,
            status='completed'
        )
        
        CategoryService.sync_category_job_counts()
        
        self.category1.refresh_from_db()
        self.assertEqual(self.category1.job_count, 2)


class OrderServiceTestCase(TestCase):
    
    def setUp(self):
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='pass123'
        )
        Profile.objects.create(user=self.employer, role='employer')
        
        self.category = Category.objects.create(
            name='Programming',
            description='Programming jobs',
            job_count=0
        )
        
        self.order = Order.objects.create(
            employer=self.employer,
            title='Test Order',
            description='Test Description',
            budget=Decimal('1000.00'),
            category=self.category,
            status='open'
        )
    
    def test_get_orders_by_category(self):
        orders = OrderService.get_orders_by_category(category=self.category.id)
        self.assertEqual(orders.count(), 1)
        self.assertEqual(orders.first().title, 'Test Order')
    
    def test_get_orders_all(self):
        orders = OrderService.get_orders_by_category()
        self.assertEqual(orders.count(), 1)
    
    def test_get_user_orders(self):
        orders = OrderService.get_user_orders(self.employer)
        self.assertEqual(orders.count(), 1)
        self.assertEqual(orders.first().employer, self.employer)
    
    def test_create_order(self):
        order_data = {
            'employer': self.employer,
            'title': 'New Order',
            'description': 'New Description',
            'budget': Decimal('2000.00'),
            'category': self.category
        }
        
        initial_job_count = self.category.job_count
        order = OrderService.create_order(order_data)
        
        self.assertEqual(order.title, 'New Order')
        self.assertEqual(order.status, 'open')
        
        self.category.refresh_from_db()
        self.assertEqual(self.category.job_count, initial_job_count + 1)
    
    def test_delete_order(self):
        initial_job_count = self.category.job_count
        OrderService.delete_order(self.order, self.employer)
        
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())
        
        self.category.refresh_from_db()
        self.assertEqual(self.category.job_count, initial_job_count - 1)
    
    def test_delete_order_permission_denied(self):
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        Profile.objects.create(user=other_user, role='employer')
        
        with self.assertRaises(ValidationError) as context:
            OrderService.delete_order(self.order, other_user)
        
        self.assertIn('permission', str(context.exception).lower())
    
    def test_update_order_status_valid_transition(self):
        updated_order = OrderService.update_order_status(
            self.order, 
            'in_progress', 
            self.employer
        )
        
        self.assertEqual(updated_order.status, 'in_progress')
    
    def test_update_order_status_invalid_transition(self):
        with self.assertRaises(ValidationError) as context:
            OrderService.update_order_status(
                self.order, 
                'completed',
                self.employer
            )
        
        self.assertIn('transition', str(context.exception).lower())
    
    def test_update_order_status_permission_denied(self):
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        Profile.objects.create(user=other_user, role='employer')
        
        with self.assertRaises(ValidationError) as context:
            OrderService.update_order_status(self.order, 'in_progress', other_user)
        
        self.assertIn('permission', str(context.exception).lower())
    
    def test_get_total_job_count(self):
        Order.objects.create(
            employer=self.employer,
            title='Job 2',
            description='Description',
            budget=Decimal('1500.00'),
            category=self.category,
            status='open'
        )
        Order.objects.create(
            employer=self.employer,
            title='Job 3',
            description='Description',
            budget=Decimal('2000.00'),
            category=self.category,
            status='completed'
        )
        
        total_count = OrderService.get_total_job_count()
        self.assertEqual(total_count, 2)
    
    def test_get_worker_accepted_orders(self):
        worker = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='pass123'
        )
        Profile.objects.create(user=worker, role='worker')
        
        application = OrderApplication.objects.create(
            order=self.order,
            worker=worker,
            cover_letter='Test cover letter',
            status='accepted'
        )
        
        accepted_orders = OrderService.get_worker_accepted_orders(worker)
        self.assertEqual(accepted_orders.count(), 1)
        self.assertEqual(accepted_orders.first().id, self.order.id)


class OrderApplicationServiceTestCase(TestCase):
    
    def setUp(self):
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='pass123'
        )
        Profile.objects.create(user=self.employer, role='employer')
        
        self.worker = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='pass123'
        )
        Profile.objects.create(user=self.worker, role='worker')
        
        self.category = Category.objects.create(
            name='Programming',
            description='Programming jobs'
        )
        
        self.order = Order.objects.create(
            employer=self.employer,
            title='Test Order',
            description='Test Description',
            budget=Decimal('1000.00'),
            category=self.category,
            status='open'
        )
        
        self.application = OrderApplication.objects.create(
            order=self.order,
            worker=self.worker,
            cover_letter='Test cover letter',
            status='pending'
        )
    
    def test_get_employer_applications(self):
        applications = OrderApplicationService.get_employer_applications(self.employer)
        self.assertEqual(applications.count(), 1)
        self.assertEqual(applications.first().worker, self.worker)
    
    def test_get_applications_by_order(self):
        applications = OrderApplicationService.get_applications_by_order(
            self.order.id, 
            self.employer
        )
        self.assertEqual(applications.count(), 1)
    
    def test_get_worker_applications(self):
        applications = OrderApplicationService.get_worker_applications(self.worker)
        self.assertEqual(applications.count(), 1)
        self.assertEqual(applications.first().order, self.order)
    
    def test_accept_application(self):
        application, order = OrderApplicationService.accept_application(
            self.application, 
            self.employer
        )
        
        self.assertEqual(application.status, 'accepted')
        self.assertEqual(order.status, 'in_progress')
    
    def test_accept_application_rejects_others(self):
        worker2 = User.objects.create_user(
            username='worker2',
            email='worker2@example.com',
            password='pass123'
        )
        Profile.objects.create(user=worker2, role='worker')
        
        application2 = OrderApplication.objects.create(
            order=self.order,
            worker=worker2,
            cover_letter='Another cover letter',
            status='pending'
        )
        
        OrderApplicationService.accept_application(self.application, self.employer)
        
        application2.refresh_from_db()
        self.assertEqual(application2.status, 'rejected')
    
    def test_accept_application_permission_denied(self):
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        Profile.objects.create(user=other_user, role='employer')
        
        with self.assertRaises(ValidationError) as context:
            OrderApplicationService.accept_application(self.application, other_user)
        
        self.assertIn('permission', str(context.exception).lower())
    
    def test_accept_application_order_not_open(self):
        self.order.status = 'completed'
        self.order.save()
        
        with self.assertRaises(ValidationError) as context:
            OrderApplicationService.accept_application(self.application, self.employer)
        
        self.assertIn('no longer open', str(context.exception).lower())
    
    def test_reject_application(self):
        application = OrderApplicationService.reject_application(
            self.application, 
            self.employer
        )
        
        self.assertEqual(application.status, 'rejected')
    
    def test_reject_application_permission_denied(self):
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='pass123'
        )
        Profile.objects.create(user=other_user, role='employer')
        
        with self.assertRaises(ValidationError) as context:
            OrderApplicationService.reject_application(self.application, other_user)
        
        self.assertIn('permission', str(context.exception).lower())
    
    def test_reject_non_pending_application(self):
        self.application.status = 'accepted'
        self.application.save()
        
        with self.assertRaises(ValidationError) as context:
            OrderApplicationService.reject_application(self.application, self.employer)
        
        self.assertIn('pending', str(context.exception).lower())
    
    def test_create_application(self):
        worker2 = User.objects.create_user(
            username='worker2',
            email='worker2@example.com',
            password='pass123'
        )
        Profile.objects.create(user=worker2, role='worker')
        
        application_data = {
            'order': self.order,
            'worker': worker2,
            'cover_letter': 'New cover letter'
        }
        
        application = OrderApplicationService.create_application(application_data)
        
        self.assertEqual(application.order, self.order)
        self.assertEqual(application.worker, worker2)
        self.assertEqual(application.status, 'pending')


class ReviewServiceTestCase(TestCase):
    
    def setUp(self):
        self.employer = User.objects.create_user(
            username='employer',
            email='employer@example.com',
            password='pass123'
        )
        Profile.objects.create(user=self.employer, role='employer')
        
        self.worker = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='pass123'
        )
        Profile.objects.create(user=self.worker, role='worker')
        
        self.category = Category.objects.create(
            name='Programming',
            description='Programming jobs'
        )
        
        self.order = Order.objects.create(
            employer=self.employer,
            title='Test Order',
            description='Test Description',
            budget=Decimal('1000.00'),
            category=self.category,
            status='completed'
        )
        
        self.application = OrderApplication.objects.create(
            order=self.order,
            worker=self.worker,
            cover_letter='Test cover letter',
            status='accepted'
        )
    
    def test_create_review(self):
        review_data = {
            'order': self.order,
            'rating': 5,
            'comment': 'Great work!'
        }
        
        review = ReviewService.create_review(review_data, self.employer)
        
        self.assertEqual(review.order, self.order)
        self.assertEqual(review.reviewer, self.employer)
        self.assertEqual(review.worker, self.worker)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Great work!')
    
    def test_create_review_no_accepted_worker(self):
        order2 = Order.objects.create(
            employer=self.employer,
            title='Order 2',
            description='Description',
            budget=Decimal('1500.00'),
            category=self.category,
            status='completed'
        )
        
        review_data = {
            'order': order2,
            'rating': 5,
            'comment': 'Great work!'
        }
        
        with self.assertRaises(ValidationError) as context:
            ReviewService.create_review(review_data, self.employer)
        
        self.assertIn('No accepted worker', str(context.exception))
    
    def test_get_user_reviews_employer(self):
        Review.objects.create(
            order=self.order,
            reviewer=self.employer,
            worker=self.worker,
            rating=5,
            comment='Great work!'
        )
        
        reviews = ReviewService.get_user_reviews(self.employer)
        self.assertEqual(reviews.count(), 1)
        self.assertEqual(reviews.first().reviewer, self.employer)
    
    def test_get_user_reviews_worker(self):
        Review.objects.create(
            order=self.order,
            reviewer=self.employer,
            worker=self.worker,
            rating=5,
            comment='Great work!'
        )
        
        reviews = ReviewService.get_user_reviews(self.worker)
        self.assertEqual(reviews.count(), 1)
        self.assertEqual(reviews.first().worker, self.worker)
    
    def test_get_user_reviews_filter_by_order(self):
        Review.objects.create(
            order=self.order,
            reviewer=self.employer,
            worker=self.worker,
            rating=5,
            comment='Great work!'
        )
        
        reviews = ReviewService.get_user_reviews(
            self.employer, 
            order_id=self.order.id
        )
        self.assertEqual(reviews.count(), 1)
    
    def test_get_user_reviews_filter_by_worker(self):
        Review.objects.create(
            order=self.order,
            reviewer=self.employer,
            worker=self.worker,
            rating=5,
            comment='Great work!'
        )
        
        reviews = ReviewService.get_user_reviews(
            self.employer, 
            worker_id=self.worker.id
        )
        self.assertEqual(reviews.count(), 1)


class ModelTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass123'
        )
    
    def test_profile_creation(self):
        profile = Profile.objects.create(
            user=self.user,
            role='employer',
            phone='+77001234567',
            city='almaty'
        )
        
        self.assertEqual(str(profile), 'testuser')
        self.assertEqual(profile.role, 'employer')
    
    def test_category_creation(self):
        category = Category.objects.create(
            name='Programming',
            description='Programming jobs'
        )
        
        self.assertEqual(str(category), 'Programming')
        self.assertEqual(category.job_count, 0)
    
    def test_order_creation(self):
        Profile.objects.create(user=self.user, role='employer')
        category = Category.objects.create(name='Programming')
        
        order = Order.objects.create(
            employer=self.user,
            title='Test Order',
            description='Description',
            budget=Decimal('1000.00'),
            category=category
        )
        
        self.assertEqual(str(order), 'Test Order (testuser)')
        self.assertEqual(order.status, 'open')
    
    def test_order_application_unique_constraint(self):
        Profile.objects.create(user=self.user, role='employer')
        worker = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='pass123'
        )
        Profile.objects.create(user=worker, role='worker')
        
        category = Category.objects.create(name='Programming')
        order = Order.objects.create(
            employer=self.user,
            title='Test Order',
            description='Description',
            budget=Decimal('1000.00'),
            category=category
        )
        
        OrderApplication.objects.create(
            order=order,
            worker=worker,
            cover_letter='First application'
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            OrderApplication.objects.create(
                order=order,
                worker=worker,
                cover_letter='Second application'
            )
    
    def test_review_one_to_one_constraint(self):
        Profile.objects.create(user=self.user, role='employer')
        worker = User.objects.create_user(
            username='worker',
            email='worker@example.com',
            password='pass123'
        )
        Profile.objects.create(user=worker, role='worker')
        
        category = Category.objects.create(name='Programming')
        order = Order.objects.create(
            employer=self.user,
            title='Test Order',
            description='Description',
            budget=Decimal('1000.00'),
            category=category
        )
        
        Review.objects.create(
            order=order,
            reviewer=self.user,
            worker=worker,
            rating=5,
            comment='Great!'
        )
        
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Review.objects.create(
                order=order,
                reviewer=self.user,
                worker=worker,
                rating=4,
                comment='Good!'
            )