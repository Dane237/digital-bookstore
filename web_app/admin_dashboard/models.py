from django.db import models
from django.contrib.auth.models import AbstractUser

# 🌟 1. USER PROFILE: Inherits Django's robust authentication while matching your team's constraints
class User(models.Model):
    ROLE_CHOICES = [
        ('Customer', 'Customer'),
        ('Staff', 'Staff'),
        ('Admin', 'Admin'),
    ]
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Customer')
    employee_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


# 🏢 2. DEPARTMENT TABLE
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


# 📚 3. BOOK TABLE
class Book(models.Model):
    isbn = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    cover_img = models.CharField(max_length=500, blank=True, null=True)
    departments = models.ManyToManyField(Department, related_name='books')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# 📦 4. ORDER TABLE: Maps directly to Section 5
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Ready for Pickup', 'Ready for Pickup'),
        ('Picked Up', 'Picked Up'),
        ('Cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    stripe_payment_id = models.CharField(max_length=255, blank=True, null=True)
    pickup_pin = models.CharField(max_length=10)
    prepared_location = models.CharField(max_length=255, blank=True, null=True)
    
    # Staff relationships mapped back to your user table profiles
    prepared_by_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='prepared_orders')
    released_by_staff = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='released_orders')
    picked_up_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"


# 🛒 5. ORDER ITEM TABLE: Section 6 Bridge
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name='order_entries')
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.book.title} (Order #{self.order.id})"
