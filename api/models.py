from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
class UserRole(models.TextChoices):
    ADMIN = 'admin'
    OPERATOR = 'operator'
    USER = 'user'

class OrderStatus(models.TextChoices):
    BOOKED = 'booked'
    TAKEN = 'taken'
    RETURNED = 'returned'

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.USER)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='api_users_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='api_users_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def __str__(self):
        return self.username

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    quantity = models.IntegerField(default=1)  
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  
    def __str__(self):
        return self.title

class Order(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    book = models.ForeignKey('Book', on_delete=models.CASCADE)
    order_date = models.DateTimeField(default=timezone.now)  
    status = models.CharField(max_length=20, choices=OrderStatus.choices, default=OrderStatus.BOOKED)
    taken_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    penalty = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    rating = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} by {self.user}"
