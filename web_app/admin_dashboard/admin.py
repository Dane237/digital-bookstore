from django.contrib import admin
from .models import Book, Order, Department  # Imports your database tables

# 🎯 CRITICAL SYSTEM REGISTRATION: This tells Django to print your bookstore tables on your admin site layout!
admin.site.register(Book)
admin.site.register(Order)
admin.site.register(Department)
