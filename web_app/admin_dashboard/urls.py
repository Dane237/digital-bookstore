from django.urls import path
from . import views

urlpatterns = [
    
    path('', views.dashboard_index_view, name='dashboard_home'),

    
    path('inventory/', views.inventory_dashboard_view, name='inventory_dashboard'),
    
    
    path('catalog/', views.catalog_view, name='catalog_view'),
    
    
    path('orders/', views.orders_view, name='orders'),
    
    
    path('import-csv/', views.import_books_csv_backend, name='import_books_csv_backend'),
    
    
    path('add-book/', views.add_book_backend, name='add_book_backend'),
    
    
    path('edit-book/<int:book_id>/', views.edit_book_backend, name='edit_book_backend'),
    
    
    path('delete-book/<int:book_id>/', views.delete_book_backend, name='delete_book_backend'),
    
    
    path('bulk-update-books/', views.bulk_update_books_backend, name='bulk_update_books_backend'),

    
    path('change-order-status/<int:order_id>/', views.change_order_status_backend, name='change_order_status_backend'),

    
    path('seed-database-orders-now/', views.auto_seed_orders_view, name='auto_seed_orders_view'),

     
    path('orders/<int:order_id>/update-location/', views.update_order_location_backend, name='update_order_location_backend'),

   
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),

    path('settings/', views.account_settings_view, name='admin_settings'),


]
