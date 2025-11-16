from django.db import models 
from django.contrib.auth.models import User

ROLE_CHOICES = [
    ('employer', 'Employer'),
    ('worker', 'Worker'),
]

CITY_CHOICES = [
    ('almaty', 'Алматы'),
    ('astana', 'Астана'),
    ('shymkent', 'Шымкент'),
    ('karaganda', 'Караганда'),
    ('pavlodar', 'Павлодар'),
    ('semey', 'Семей'),
    ('aktau', 'Актау'),
    ('aktobe', 'Актобе'),
    ('atyrau', 'Атырау'),
    ('kostanay', 'Костанай'),
    ('kokshetau', 'Кокшетау'),
    ('taraz', 'Тараз'),
    ('uralsk', 'Уральск'),
    ('petropavlovsk', 'Петропавловск'),
    ('temirtau', 'Темиртау'),
    ('taldykorgan', 'Талдыкорган'),
    ('jezkazgan', 'Жезказган'),
    ('ekibastuz', 'Экибастуз'),
    ('kzylorda', 'Кызылорда'),
    ('ust-kamenogorsk', 'Усть-Каменогорск'),
    ('zhanaozen', 'Жанаозен'),
    ('turan', 'Туран'),
]

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    city = models.CharField(max_length=50,choices=CITY_CHOICES, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}"
   

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Order(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    employer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        limit_choices_to={'profile__role': 'employer'},
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.employer})"


class OrderApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    worker = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='applications',
        limit_choices_to={'profile__role': 'worker'}, 
    )
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('order', 'worker')  # один воркер = одна заявка на заказ

    def __str__(self):
        return f"{self.worker} → {self.order.title} ({self.status})"

class Review(models.Model):
    RATING_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'profile__role': 'employer'})
    worker = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer.username} for {self.worker.username}"

