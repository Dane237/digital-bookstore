from django.urls import path
from . import views

urlpatterns = [
    # 📊 1. MAIN ANALYTICAL SUMMARY DASHBOARD (Fixed to match your views.py function name!)
    path('', views.dashboard_index_view, name='dashboard_home'),

    
    # 📦 2. BOOKSTOCK INVENTORY MANAGEMENT GRID LEDGER (🎯 FIXED: Given its own separate url path)
    path('inventory/', views.inventory_dashboard_view, name='inventory_dashboard'),
    
    # 📖 3. PUBLIC STOREFRONT PRODUCT CARDS GRID CATALOG
    path('catalog/', views.catalog_view, name='catalog_view'),
    
    # 📥 4. REAL-TIME STUDENT TRANSACTION STATUS LIFECYCLE TRACKER
    path('orders/', views.orders_view, name='orders'),
    
    # 📄 BULK CSV UPLOAD PATHWAY LINK
    path('import-csv/', views.import_books_csv_backend, name='import_books_csv_backend'),
    
    # ➕ THE ADD BOOK ROUTE LINK 
    path('add-book/', views.add_book_backend, name='add_book_backend'),
    
    # 📝 POPUP EDIT ROUTE CELL LINK
    path('edit-book/<int:book_id>/', views.edit_book_backend, name='edit_book_backend'),
    
    # 🗑️ DELETION TRACK SYSTEM LINK 
    path('delete-book/<int:book_id>/', views.delete_book_backend, name='delete_book_backend'),
    
    # 🎛️ SYSTEM BULK BATCH OPERATION LINK PATH
    path('bulk-update-books/', views.bulk_update_books_backend, name='bulk_update_books_backend'),

    # 📦 STUDENT TRANSACTION LIFECYCLE LINK CONTROL
    path('change-order-status/<int:order_id>/', views.change_order_status_backend, name='change_order_status_backend'),

    # 🌱 AUTOMATED BACKGROUND SYSTEM DATA SEEDER PATHWAY
    path('seed-database-orders-now/', views.auto_seed_orders_view, name='auto_seed_orders_view'),

        # 📍 STORAGE LOCATION ASSIGNMENT UPDATER LINK PATH
    path('orders/<int:order_id>/update-location/', views.update_order_location_backend, name='update_order_location_backend'),

    # 🔐 Standalone Admin Back-Office Entrance Portals
    path('login/', views.admin_login_view, name='admin_login'),
    path('logout/', views.admin_logout_view, name='admin_logout'),

    path('settings/', views.account_settings_view, name='admin_settings'),


]
