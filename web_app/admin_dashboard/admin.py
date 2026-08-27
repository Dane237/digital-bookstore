from django.contrib import admin
from .models import Book, Order, Department, OrderItem  # Imports database tables

# CRITICAL SYSTEM REGISTRATION
admin.site.register(Book)
admin.site.register(Order)
admin.site.register(Department)
admin.site.register(OrderItem)