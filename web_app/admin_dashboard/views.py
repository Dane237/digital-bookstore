import requests
from django.shortcuts import render, redirect
from .models import Book, Department
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required


def inventory_dashboard_view(request):
    """
    MASTER SYNC VIEW: Focuses strictly on pulling dynamic books 
    and department category matrices straight from PostgreSQL tables.
    """
    all_books = Book.objects.all().order_by('-id')
    all_depts = Department.objects.all().order_by('name')
    
    return render(request, 'inventory.html', {
        'books': all_books,
        'departments': all_depts
    })


from django.shortcuts import render
from django.db.models import Q
from .models import Order

def orders_view(request):
    """
    ORDERS DASHBOARD VIEW: Fetches, filters, and searches student 
    transactions out of PostgreSQL database simultaneously.
    """
    # Grab incoming search queries or active status tab parameters
    search_query = request.GET.get('search_q', '').strip()
    status_filter = request.GET.get('status', 'All')

    # Pull all order logs out of your database, newest records first
    all_orders = Order.objects.all().order_by('-id')

    # STEP A: APPLY LIVE MULTI-COLUMN SEARCH FILTER
    if search_query:
        # Check if the user typed a pure numeric string (like '5' or '00005') to search by ID safely
        if search_query.isdigit():
            # Strips leading zeros out so it can cast and match PostgreSQL Integer Primary Keys perfectly
            clean_id = int(search_query)
            all_orders = all_orders.filter(Q(id=clean_id) | Q(pickup_pin__icontains=search_query))
        else:
            # Fallback search constraint matching against your pickup pin code text column specifically
            all_orders = all_orders.filter(pickup_pin__icontains=search_query)

    # STEP B: APPLY DYNAMIC STATUS TAB FILTERS
    if status_filter != 'All':
        all_orders = all_orders.filter(status=status_filter)

    # Calculate live notification counts for your filter tab badges
    pending_count = Order.objects.filter(status='Pending').count()
    ready_count = Order.objects.filter(status='Ready for Pickup').count()
    completed_count = Order.objects.filter(status='Picked Up').count()

    return render(request, 'orders.html', {
        'orders': all_orders,
        'current_filter': status_filter,
        'search_query': search_query, # Preserves user text inputs inside the input box on submit!
        'pending_count': pending_count,
        'ready_count': ready_count,
        'completed_count': completed_count,
    })



from django.shortcuts import render
from django.db.models import Q
from .models import Book # Imports database book tracking table structure

def catalog_view(request):
    """
    STOREFRONT CATALOG VIEW: Queries inventory books from the database 
    and handles dynamic search filtering instantly.
    """
    #  Catch search text parameters from the top toolbar form input
    search_query = request.GET.get('search_catalog', '').strip()
    
    # Grab all available books ordered by newest listing first
    books = Book.objects.all().order_by('-id')
    
    # Apply search terms if entered (searches Title, Author, ISBN, and Department!)
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(departments__name__icontains=search_query)
        ).distinct()
        
    return render(request, 'catalog.html', {
        'books': books,
        'search_query': search_query
    })




def add_book_backend(request):
    if request.method == "POST":
        # Extract input text data using matching names
        title_input = request.POST.get("title")
        author_input = request.POST.get("author")
        isbn_input = request.POST.get("isbn")
        
        # LOOKUP KEYS: Ensure these match what's sent from the modal form
        price_input = request.POST.get("price", "0.00")
        stock_input = request.POST.get("stock_quantity", "0")
        
        desc_input = request.POST.get("description")
        img_input = request.POST.get("cover_img")       
        dept_input = request.POST.get("department")      

        # Create the new database record row
        new_book = Book.objects.create(
            title=title_input,
            author=author_input,
            isbn=isbn_input,
            price=price_input,
            stock_quantity=stock_input,
            description=desc_input,
            cover_img=img_input                           
        )

        #  MULTI-DEPARTMENT SPLITTER: Slices text by commas to save multiple links at once
        if dept_input:
            # Slices the text by commas into a list (e.g., ['Mathematics', 'Computer Science'])
            departments_list = [d.strip() for d in dept_input.split(",") if d.strip()]

            for dept_name in departments_list:
                dept_obj, _ = Department.objects.get_or_create(name=dept_name)
                new_book.departments.add(dept_obj)


        return redirect("inventory_dashboard")

    return redirect("inventory_dashboard")

from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, Department

def edit_book_backend(request, book_id):
    """
    POPUP EDIT CONTROLLER: Intercepts form data packets from your floating 
    edit modal card and updates the physical textbook row records inside PostgreSQL.
    """
    book_obj = get_object_or_404(Book, id=book_id)
    
    if request.method == "POST":
        # Extract the updated input data variables from text fields
        book_obj.title = request.POST.get("title")
        book_obj.author = request.POST.get("author")
        book_obj.isbn = request.POST.get("isbn")
        book_obj.price = request.POST.get("price", "0.00")
        book_obj.stock_quantity = request.POST.get("stock_quantity", "0")
        book_obj.description = request.POST.get("description")
        book_obj.cover_img = request.POST.get("cover_img")       
        
        # MULTI-DEPARTMENT EDIT SPLITTER
        dept_input = request.POST.get("department")      
        if dept_input:
            book_obj.departments.clear()  # Clear old links first
            departments_list = [d.strip() for d in dept_input.split(",") if d.strip()]
            for dept_name in departments_list:
                dept_obj, _ = Department.objects.get_or_create(name=dept_name)
                book_obj.departments.add(dept_obj)

            
        # Save updates directly to database disk clusters
        book_obj.save()
        return redirect("inventory_dashboard")
        
    return redirect("inventory_dashboard")

from django.shortcuts import get_object_or_404, redirect
from .models import Book

def delete_book_backend(request, book_id):
    """
    DATA PURGE CONTROLLER: Locates the requested textbook record row 
    by its ID and purges it permanently out of your PostgreSQL table rows.
    """
    # 1. Safely pull the requested book row, or throw a 404 if it doesn't exist
    book_obj = get_object_or_404(Book, id=book_id)
    
    # 2. Delete it completely from local system drive
    book_obj.delete()
    
    # 3. Refresh and return cleanly back onto active ledger dashboard lanes
    return redirect("inventory_dashboard")



def import_books_csv_backend(request):
    """
    BULK CSV PARSER: Intercepts an uploaded spreadsheet file, reads your 
    manually typed rows, and saves hundreds of textbooks into PostgreSQL at once.
    """
    if request.method == "POST" and request.FILES.get("csv_file"):
        csv_file = request.FILES["csv_file"]
        
        if not csv_file.name.endswith('.csv'):
            return redirect("inventory_dashboard")
            
        data_set = csv_file.read().decode('UTF-8')
        import io
        io_string = io.StringIO(data_set)
        import csv
        next(io_string) # Skip CSV Header
        
        for row in csv.reader(io_string, delimiter=','):
            if len(row) >= 5: 
                Book.objects.create(
                    title=row[0].strip(),
                    author=row[1].strip(),
                    isbn=row[2].strip(),
                    price=row[3].strip() or "0.00",
                    stock_quantity=row[4].strip() or "0",
                    description=row[5].strip() if len(row) > 5 else "",
                    cover_img=row[6].strip() if len(row) > 6 else ""
                )
                
    return redirect("inventory_dashboard")

from django.shortcuts import redirect
from .models import Book, Department

def bulk_update_books_backend(request):
    """
    UNIFIED BULK CONTROLLER: Perfectly aligned with your JavaScript modal routers
    to process mass modifications straight to your PostgreSQL database.
    """
    if request.method == "POST":
        raw_ids_string = request.POST.get("selected_book_ids_string", "").strip()
        action_type = request.POST.get("bulk_action_type_flag", "").strip()
        
        if not raw_ids_string:
            return redirect("inventory_dashboard")
            
        selected_book_ids = [int(bid.strip()) for bid in raw_ids_string.split(",") if bid.strip().isdigit()]
        
        if not selected_book_ids:
            return redirect("inventory_dashboard")

        # -------------------------------------------------------------
        # ACTION A: Bulk Row Purge (MATCHES 'bulk_delete')
        # -------------------------------------------------------------
        if action_type == "bulk_delete":
            Book.objects.filter(id__in=selected_book_ids).delete()
            
        
        # ACTION B: Mass Assign Checklist Departments (Reads list arrays seamlessly!)
        elif action_type == "bulk_assign_department":
            #  FIX: Changed .get() to .getlist() to read multiple checked checkboxes simultaneously!
            departments_list = request.POST.getlist("bulk_department_value")
            
            if departments_list:
                book_records = Book.objects.filter(id__in=selected_book_ids)
                for book_obj in book_records:
                    for dept_name in departments_list:
                        dept_obj, _ = Department.objects.get_or_create(name=dept_name.strip())
                        book_obj.departments.add(dept_obj)


       
         # -------------------------------------------------------------
        # ACTION METHOD C: Bulk Stock Quantity Adjustments
        # -------------------------------------------------------------
        elif action_type == "bulk_stock":
            stock_input_val = request.POST.get("bulk_stock_value", "").strip()
            strategy_type = request.POST.get("bulk_stock_strategy", "add").strip()
            
            if stock_input_val.isdigit():
                target_amount = int(stock_input_val)
                book_records = Book.objects.filter(id__in=selected_book_ids)
                
                for book_obj in book_records:
                    if strategy_type == "set":
                        # CHOICE PATH A: Direct physical box reset (e.g., Exactly 15 items left)
                        book_obj.stock_quantity = max(0, target_amount)
                    else:
                        # CHOICE PATH B: Incremental stacking additions (e.g., Adding +10 more items)
                        book_obj.stock_quantity = max(0, book_obj.stock_quantity + target_amount)
                        
                    book_obj.save()

        
         # -------------------------------------------------------------
        #  ACTION METHOD D: Advanced Price Matrix Adjustments
        # -------------------------------------------------------------
        elif action_type == "bulk_price":
            fixed_amount_input = request.POST.get("bulk_price_value", "").strip().replace("$", "")
            percentage_value_input = request.POST.get("bulk_percentage_value", "").strip()
            percentage_type = request.POST.get("bulk_percentage_type", "").strip()
            
            book_records = Book.objects.filter(id__in=selected_book_ids)
            from decimal import Decimal

            # CHOICE PATH A: Apply percentage markdown or markup calculations
            if percentage_value_input.isdigit():
                percent_factor = Decimal(percentage_value_input) / Decimal("100")
                
                for book_obj in book_records:
                    current_price = Decimal(str(book_obj.price))
                    
                    if percentage_type == "markdown":
                        # Apply a percentage discount (e.g., -10%)
                        new_calculated_price = current_price * (Decimal("1") - percent_factor)
                    else:
                        # Apply a percentage increase (e.g., +10%)
                        new_calculated_price = current_price * (Decimal("1") + percent_factor)
                        
                    # Clamp calculation output to protect against negative dollar anomalies
                    book_obj.price = max(Decimal("0.00"), round(new_calculated_price, 2))
                    book_obj.save()
                    
            # CHOICE PATH B: Direct, rigid fixed value overwrite
            elif fixed_amount_input:
                try:
                    clean_fixed_price = round(Decimal(fixed_amount_input), 2)
                    Book.objects.filter(id__in=selected_book_ids).update(price=clean_fixed_price)
                except:
                    pass # Gracefully catch input formatting issues


        return redirect("inventory_dashboard")
        
    return redirect("inventory_dashboard")

from django.db.models import Q
from .models import Book, Department

def inventory_dashboard_view(request):
    """
     CORE INVENTORY VIEW: Lists catalog items and dynamically handles
    the top toolbar's live search filter matrix.
    """
    #  Catch the incoming query text from top toolbar field box
    search_query = request.GET.get('search_inventory', '').strip()
    
    # Start by grabbing all books ordered by newest first
    books = Book.objects.all().order_by('-id')
    departments = Department.objects.all().order_by('name')
    
        #  MULTI-COLUMN RELATIONSHIP FILTER ENGINE (Case-Insensitive Across All Databases)
    if search_query:
        books = books.filter(
            Q(title__icontains=search_query) |
            Q(author__icontains=search_query) |
            Q(isbn__icontains=search_query) |
            Q(departments__name__icontains=search_query)
        ).distinct()

        
    return render(request, 'inventory.html', {
        'books': books,
        'departments': departments,
        'search_query': search_query  # Pass back down to preserve the text inside the input box
    })

from django.shortcuts import redirect, get_object_or_404
from .models import Order # Ensure your Order model name matches exactly!

def change_order_status_backend(request, order_id):
    """
     ORDER STATUS LIFE CYCLE ENGINE: Updates records using your exact database model field keys.
    """
    if request.method == "POST":
        order_obj = get_object_or_404(Order, id=order_id)
        action_type = request.POST.get("status_action_flag")
        
        # Advance Step A: Shifting 'Pending' -> 'Ready for Pickup'
        if action_type == "advance_to_ready":
            order_obj.status = "Ready for Pickup"
            order_obj.save()
            
        # Advance Step B: Shifting 'Ready for Pickup' -> 'Picked Up' (Completed)
        elif action_type == "advance_to_completed":
            order_obj.status = "Picked Up"
            order_obj.save()
            
        # Hard Purge: Remove record from log
        elif action_type == "cancel_order":
            order_obj.status = "Cancelled"
            order_obj.save()
            
        return redirect("orders")
        
    return redirect("orders")

from django.http import HttpResponse
from django.contrib.auth import get_user_model
from .models import Order

def auto_seed_orders_view(request):
    """
     FOOLPROOF DATA SEEDER VIEW: Programmatically forces a master user 
    and two mock textbook orders to write directly into your database.
    """
    #  1. Resolve and secure the exact Custom User Model class instance database expects
    UserClass = get_user_model()
    
    #  Try to look up the specific 'admin' user profile account directly
    valid_user = UserClass.objects.filter(username='admin').first()
    
    # Fallback safety guard: if somehow no account exists, pull the absolute first user row record
    if not valid_user:
        valid_user = UserClass.objects.first()
        
    # Absolute emergency backup fallback: if the database is completely empty, create an admin profile row
    if not valid_user:
        valid_user = UserClass.objects.create_superuser(
            username='admin',
            email='admin@puc.edu.kh',
            password='password123'
        )

    #  2. Generate a 'Pending' student transaction record row
    Order.objects.create(
        user=valid_user,  #  FIXED: Relies on the resolved custom user object class
        status="Pending",
        total_amount="45.95",
        prepared_location="Shelf A1",
        pickup_pin="849201" 
    )

    #  3. Generate a 'Ready for Pickup' student transaction record row
    Order.objects.create(
        user=valid_user,  #  FIXED: Relies on the resolved custom user object class
        status="Ready for Pickup",
        total_amount="12.00",
        prepared_location="Shelf B3",
        pickup_pin="302941" 
    )

    return HttpResponse(
        f"<h2 style='color:#16163f; font-family:sans-serif; text-align:center; margin-top:20vh;'>"
        f"🎉 SUCCESS! Database updated seamlessly.<br>"
        f"Current Total Orders in PostgreSQL: {Order.objects.count()}</h2>"
    )





from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from .models import Order

@require_POST
def update_order_location_backend(request, order_id):
    """
     INLINE STORAGE ASSIGNER: Updates the shelf slot values
    directly inside your PostgreSQL table rows.
    """
    order = get_object_or_404(Order, id=order_id)
    new_loc = request.POST.get('new_prepared_location', '').strip()
    
    order.prepared_location = new_loc if new_loc else None
    order.save()
    
    return redirect('orders')


from django.shortcuts import render
from django.db.models import Sum
from django.utils import timezone
from .models import Order, Book

@login_required
def dashboard_index_view(request):
    """
     MAIN ANALYTICS CONTROLLER: Computes real-time aggregates straight out of
    PostgreSQL to feed your metric counters, ratios, and live calendar trend charts.
    """
        # 🌍 THE CORRECTION: Translate current time to your local clock BEFORE stripping the hours!
    local_now = timezone.localtime(timezone.now())
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)

    # CARD 1: Today's Books Sold Counter (Counts nested item quantity volumes sold today)
    todays_orders_query = Order.objects.filter(order_date__gte=today_start).exclude(status='Cancelled')
    books_sold_today = sum(sum(item.quantity for item in order.items.all()) for order in todays_orders_query)


    #  CARD 2: Total Stock Counter (Sums absolute inventory volumes from Book table)
    total_stock = Book.objects.aggregate(total=Sum('stock_quantity'))['total'] or 0

    #  CARD 3: Today's Earnings Ledger (Sums financial amounts processed since midnight)
    todays_earnings = Order.objects.filter(
        order_date__gte=today_start
    ).exclude(
        status='Cancelled'
    ).aggregate(total=Sum('total_amount'))['total'] or 0.00

    #  CARDS 4 & 5: Back-Office Live Backlog Status Counters
    pending_count = Order.objects.filter(status='Pending').count()
    ready_count = Order.objects.filter(status='Ready for Pickup').count()
    
    #  CARD 6: Today's Completed Pickups (Filters strictly to count ONLY today's pick ups!)
    completed_count = Order.objects.filter(status='Picked Up', order_date__gte=today_start).count()

    # 4. FULFILLMENT QUEUE RATIO GRAPH CALCULATIONS
    total_active_orders = pending_count + ready_count + completed_count or 1
    pending_pct = (pending_count / total_active_orders) * 100
    ready_pct = (ready_count / total_active_orders) * 100
    completed_pct = (completed_count / total_active_orders) * 100

    #  5. DYNAMIC REVENUE GRAPH NODES (Groups sales data by each individual day of the week)
    try:
        week_offset = int(request.GET.get('week', 0))
    except ValueError:
        week_offset = 0

    local_now = timezone.localtime(timezone.now())
    target_date = local_now + timezone.timedelta(weeks=week_offset)
    current_weekday = target_date.weekday()
    
    monday_date = (target_date - timezone.timedelta(days=current_weekday)).replace(hour=0, minute=0, second=0, microsecond=0)
    sunday_date = monday_date + timezone.timedelta(days=6, hours=23, minutes=59, seconds=59)

    days_labels = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    days_revenue = {f'rev_{label}': 0.00 for label in days_labels}
    
    # Query database records bounded within your selected filter week calendar track
    weekly_orders = Order.objects.filter(
        order_date__gte=monday_date,
        order_date__lte=sunday_date
    ).exclude(status='Cancelled')

    for order in weekly_orders:
        order_local_date = timezone.localtime(order.order_date)
        day_name = order_local_date.strftime('%a').lower()
        key = f'rev_{day_name}'
        if key in days_revenue:
            days_revenue[key] += float(order.total_amount)

    # Determine peak day value to scale graph bar percentages cleanly
    peak_value = max(days_revenue.values()) or 100.00
    
    for label in days_labels:
        days_revenue[f'{label}_pct'] = (days_revenue[f'rev_{label}'] / peak_value) * 85 + 5

    
    #  UPDATED: Tightens the filter boundary rule to isolate ONLY items under 2 copies left!
    low_stock_alerts = Book.objects.filter(stock_quantity__lt=2).order_by('stock_quantity')[:5]


    # Combine all variables into a single context dictionary bundle
    context = {
        'books_sold_today': books_sold_today,
        'total_stock': total_stock,
        'todays_earnings': todays_earnings,
        'pending_count': pending_count,
        'ready_count': ready_count,
        'completed_count': completed_count,
        'pending_pct': pending_pct,
        'ready_pct': ready_pct,
        'completed_pct': completed_pct,
        'low_stock_alerts': low_stock_alerts,
        'week_offset': week_offset,
        'monday_date': monday_date,
    }
    context.update(days_revenue)  # Merges weekday calculation variables right into template keys

    return render(request, 'dashboard_index.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard_home')
        
    if request.method == 'POST':
        user_str = request.POST.get('username')
        pass_str = request.POST.get('password')
        
        user = authenticate(request, username=user_str, password=pass_str)
        
        if user is not None:
            if user.is_staff:
                auth_login(request, user)
                return redirect('dashboard_home')
            else:
                return render(request, 'admin_login.html', {'error': 'Access Denied: Account lacks Staff clearances.'})
        else:
            return render(request, 'admin_login.html', {'error': 'Invalid administrative credentials.'})
            
    return render(request, 'admin_login.html')

def admin_logout_view(request):
    auth_logout(request)
    return redirect('admin_login')

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required(login_url='admin_login')
def account_settings_view(request):
    user = request.user
    
    if request.method == 'POST':
        form_kind = request.POST.get('form_type')
        
        # 👤 HANDLER 1: PROFILE FORM SUBMISSION
        if form_kind == 'profile_update':
            new_username = request.POST.get('username', '').strip()
            new_email = request.POST.get('email', '').strip()
            
            if new_username and new_email:
                user.username = new_username
                user.email = new_email
                user.save()
                messages.success(request, 'Profile contact card parameters saved successfully!')
            else:
                messages.error(request, 'Error: Fields cannot be left blank.')
            return redirect('admin_settings')
            
        # 🔒 HANDLER 2: SECURITY PASSWORD FORM SUBMISSION
        elif form_kind == 'password_update':
            curr_pass = request.POST.get('current_password', '')
            new_pass = request.POST.get('new_password', '')
            conf_pass = request.POST.get('confirm_password', '')
            
            # Cryptographically cross-check the current password row inside PostgreSQL
            if user.check_password(curr_pass):
                if new_pass == conf_pass:
                    user.set_password(new_pass)
                    user.save()
                    # 🔥 CRITICAL: Updates your session cookie hash so Django doesn't log you out!
                    update_session_auth_hash(request, user) 
                    messages.success(request, 'Administrative master security keys rotated successfully!')
                else:
                    messages.error(request, 'Validation Failure: New password fields do not match!')
            else:
                messages.error(request, 'Authentication Refused: Incorrect current security password!')
            return redirect('admin_settings')
            
    context = {
        'admin_user': user,
    }
    return render(request, 'account_settings.html', context)

