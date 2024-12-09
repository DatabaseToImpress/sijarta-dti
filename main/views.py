from django.db import connection
from django.shortcuts import render
from collections import defaultdict
from datetime import date, timedelta, datetime
from django.http import JsonResponse
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from uuid import uuid4
import json

def home_page(request):
    try:
        with connection.cursor() as cursor:
            # Fetch service categories and their subcategories
            cursor.execute("""
                SELECT 
                    sc.ServiceCategoryId AS CategoryID, 
                    c.CategoryName AS Category, 
                    sc.Id AS SubcategoryID, 
                    sc.SubcategoryName AS Subcategory
                FROM 
                    sijarta.SERVICE_CATEGORY c
                JOIN 
                    sijarta.SERVICE_SUBCATEGORY sc ON c.Id = sc.ServiceCategoryId
                ORDER BY 
                    c.CategoryName, sc.SubcategoryName;
            """)
            services = cursor.fetchall()  # List of tuples: (CategoryID, Category, SubcategoryID, Subcategory)
    except Exception as e:
        print(f"Database Error: {e}")
        services = []

    # Group services by category
    categorized_services = defaultdict(list)
    for service in services:
        category_id, category_name, subcategory_id, subcategory_name = service
        categorized_services[category_name].append((subcategory_id, subcategory_name))

    # Create a list of categories with subcategories for the dropdown
    categories_for_dropdown = [
        (category_name, subcategories) 
        for category_name, subcategories in categorized_services.items()
    ]

    # Get the selected category from the GET request, if any
    selected_category = request.GET.get('category', 'all')

    # Handle search functionality
    search_query = request.GET.get('search', '').lower()
    if search_query:
        # Filter categorized services based on the search query
        categorized_services = {
            category: [
                subcategory for subcategory in subcategories
                if search_query in subcategory[1].lower() or search_query in category.lower()
            ]
            for category, subcategories in categorized_services.items()
            if any(search_query in subcategory[1].lower() for subcategory in subcategories) or search_query in category.lower()
        }

    # Apply category filter if a category other than "All" is selected
    if selected_category != 'all':
        categorized_services = {
            category: subcategories
            for category, subcategories in categorized_services.items()
            if category.lower() == selected_category.lower()
        }

    # Manual pagination logic
    items_per_page = 10
    page_number = int(request.GET.get('page', 1))  # Default to the first page
    total_items = sum(len(subcategories) for subcategories in categorized_services.values())
    start_index = (page_number - 1) * items_per_page
    end_index = start_index + items_per_page

    # Paginate the services after search and category filtering
    paginated_services = []
    for category, subcategories in categorized_services.items():
        paginated_services.append((category, subcategories[start_index:end_index]))

    # Determine if there are more pages
    total_pages = (total_items + items_per_page - 1) // items_per_page  # Ceiling division
    has_next_page = page_number < total_pages
    has_previous_page = page_number > 1

    # Render the template with paginated data
    return render(request, 'home.html', {
        'services': paginated_services,
        'categories_for_dropdown': categories_for_dropdown,
        'search_query': search_query,
        'selected_category': selected_category,
        'current_page': page_number,
        'total_pages': total_pages,
        'has_next_page': has_next_page,
        'has_previous_page': has_previous_page,
    })


def subcategory_services_user(request, id):
    category = request.GET.get('category', None)
    subcategory = request.GET.get('subcategory', None)

    role = request.session.get('role', None)
    worker_id = request.session.get('worker_id', None)

    if request.method == "POST" and role == 'Worker' and worker_id:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT ServiceCategoryId 
                    FROM sijarta.SERVICE_SUBCATEGORY
                    WHERE Id = %s
                """, [id])
                service_category = cursor.fetchone()

                if not service_category:
                    return JsonResponse({'error': 'Invalid subcategory or service category does not exist'}, status=400)

                service_category_id = service_category[0]

                cursor.execute("""
                    SELECT 1 FROM sijarta.WORKER_SERVICE_CATEGORY
                    WHERE WorkerId = %s AND ServiceCategoryId = %s
                """, [worker_id, service_category_id])
                already_joined = cursor.fetchone()

                if already_joined:
                    return JsonResponse({'message': 'Already joined'}, status=200)

                cursor.execute("""
                    INSERT INTO sijarta.WORKER_SERVICE_CATEGORY (WorkerId, ServiceCategoryId)
                    VALUES (%s, %s)
                """, [worker_id, service_category_id])

            return JsonResponse({'message': 'Successfully joined'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    subcategory_query = """
        SELECT
            ssc.SubcategoryName, 
            ssc.Description,
            sc.CategoryName,
            sc.Id AS ServiceCategoryId
        FROM sijarta.SERVICE_SUBCATEGORY ssc
        JOIN sijarta.SERVICE_CATEGORY sc ON ssc.ServiceCategoryId = sc.Id
        WHERE ssc.Id = %s
    """
    workers_query = """
        SELECT DISTINCT au.Name
        FROM sijarta.WORKER_SERVICE_CATEGORY wsc
        JOIN sijarta.WORKER w ON w.Id = wsc.WorkerId
        JOIN sijarta.SERVICE_CATEGORY sc ON sc.Id = wsc.ServiceCategoryId
        JOIN sijarta.APP_USER au ON au.Id = w.Id
        WHERE sc.Id = (SELECT ServiceCategoryId FROM sijarta.SERVICE_SUBCATEGORY WHERE Id = %s)
    """
    sessions_query = """
        SELECT Session, Price
        FROM sijarta.SERVICE_SESSION
        WHERE SubcategoryId = %s
    """

    with connection.cursor() as cursor:
        cursor.execute(subcategory_query, [id])
        subcategory_result = cursor.fetchall()

        cursor.execute(workers_query, [id])
        workers_result = cursor.fetchall()

        cursor.execute(sessions_query, [id])
        sessions_result = cursor.fetchall()

        already_joined = False
        if role == 'Worker' and worker_id:
            cursor.execute("""
                SELECT 1 FROM sijarta.WORKER_SERVICE_CATEGORY
                WHERE WorkerId = %s AND ServiceCategoryId = %s
            """, [worker_id, subcategory_result[0][3]])
            already_joined = cursor.fetchone() is not None

    subcategory_data = {
        'subcategory_name': subcategory_result[0][0],
        'description': subcategory_result[0][1],
        'service_category': subcategory_result[0][2],
        'service_category_id': subcategory_result[0][3],
    }

    workers = list(set(worker[0] for worker in workers_result))
    sessions = [{'session': session[0], 'price': session[1]} for session in sessions_result]

    context = {
        'category': category,
        'subcategory': subcategory,
        'id': id,
        'subcategory_data': subcategory_data,
        'workers': workers,
        'sessions': sessions,
        'role': role,
        'already_joined': already_joined,
    }

    return render(request, 'subcategory_services_user.html', context)

def booking_view(request):
    from datetime import date, datetime
    import uuid

    today = date.today()
    today_str = today.strftime('%Y-%m-%d')

    # Fetch payment methods
    with connection.cursor() as cursor:
        cursor.execute("SELECT Id, Name FROM SIJARTA.PAYMENT_METHOD")
        payment_methods = cursor.fetchall()

    # Extract parameters from the query
    session = request.GET.get('session')
    price_str = request.GET.get('price')
    subcategory_service_id = request.GET.get('subcategoryServiceId')  # Fetch subcategory service ID
    price = float(price_str) if price_str else None
    price = round(price) if price is not None else None

    if request.method == "POST":
        payment_method = request.POST.get('paymentMethod')
        total_payment = request.POST.get('totalPayment')
        order_date = request.POST.get('orderDate')
        service_date = request.POST.get('serviceDate')
        service_time = request.POST.get('serviceTime')
        discount_code = request.POST.get('discountCode')
        if discount_code:
            with connection.cursor() as cursor:
                cursor.execute("SELECT Code FROM SIJARTA.DISCOUNT WHERE Code = %s", [discount_code])
                discount = cursor.fetchone()
            if not discount:
                return JsonResponse({'success': False, 'error': 'Invalid discount code'}, status=400)
        else:
            discount_code = None  # Handle cases where no discount code is provided


        customer_id = request.session.get('user_id')  # Assume customer_id is in session
        
        worker_id = None  # You may need logic to assign a worker dynamically

        if not customer_id:
            return JsonResponse({'success': False, 'error': 'Customer is not logged in'}, status=400)

        # Create a new service order
        service_order_id = str(uuid.uuid4())

        try:
            with connection.cursor() as cursor:
                # Insert data into TR_SERVICE_ORDER
                cursor.execute("""
                    INSERT INTO SIJARTA.TR_SERVICE_ORDER (
                        Id, orderDate, serviceDate, serviceTime, TotalPrice, 
                        customerId, workerId, serviceCategoryId, Session, 
                        discountCode, paymentMethodId
                    ) VALUES (
                        %s, %s, %s, %s, %s, 
                        %s, %s, %s, %s, 
                        %s, %s
                    )
                """, [
                    service_order_id, order_date, service_date, service_time, total_payment,
                    customer_id, worker_id, subcategory_service_id, session,
                    discount_code, payment_method
                ])

                # Commit the transaction
                connection.commit()

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

        # Redirect to the bookings page
        return JsonResponse({'success': True, 'redirect_url': '/main/view-bookings/'}, status=200)

    # Render booking page
    context = {
        'today': today_str,
        'payment_methods': payment_methods,
        'price': price,
        'session': session,
        'subcategoryServiceId': subcategory_service_id,
    }
    return render(request, "booking.html", context)


def view_booking(request):
    # Get the logged-in user's ID
    customer_id = request.session.get('user_id')

    # Query booking data from the database
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tso.Id AS order_id,
                   ssc.SubcategoryName AS service_name,
                   COALESCE(os.Status, 'Unknown Status') AS order_status,
                   tso.orderDate AS order_date,
                   tso.TotalPrice AS total_payment
            FROM SIJARTA.TR_SERVICE_ORDER tso
            JOIN SIJARTA.SERVICE_SESSION ss 
                ON tso.serviceCategoryId = ss.SubcategoryId AND tso.Session = ss.Session
            JOIN SIJARTA.SERVICE_SUBCATEGORY ssc 
                ON ss.SubcategoryId = ssc.Id
            LEFT JOIN (
                SELECT tos.serviceTrId,
                       tos.statusId
                FROM SIJARTA.TR_ORDER_STATUS tos
                JOIN (
                    SELECT serviceTrId, MAX(date) AS latest_date
                    FROM SIJARTA.TR_ORDER_STATUS
                    GROUP BY serviceTrId
                ) latest_status
                ON tos.serviceTrId = latest_status.serviceTrId 
                   AND tos.date = latest_status.latest_date
            ) latest_status
                ON latest_status.serviceTrId = tso.Id
            LEFT JOIN SIJARTA.ORDER_STATUS os 
                ON latest_status.statusId = os.Id
            WHERE tso.customerId = %s
        """, [customer_id])
        bookings = cursor.fetchall()

    # Prepare data for the template
    bookings_list = [
        {
            'order_id': booking[0],
            'service_name': booking[1],
            'order_status': booking[2],
            'order_date': booking[3],
            'total_payment': booking[4],
        }
        for booking in bookings
    ]

    # Send data to the template
    context = {
        'bookings': bookings_list
    }
    return render(request, 'view_booking.html', context)





def worker_profile(request, worker_name):
    # Prepare the SQL query to fetch worker data
    query = """
        SELECT 
            w.Id,
            u.Name,
            w.PicURL,
            w.Rate,
            w.TotalFinishOrder,
            u.PhoneNum,
            u.DoB,
            u.Address
        FROM SIJARTA.WORKER w
        JOIN SIJARTA.APP_USER u ON w.Id = u.Id
        WHERE u.Name = %s
    """
    
    # Execute the query and fetch results
    with connection.cursor() as cursor:
        cursor.execute(query, [worker_name])
        result = cursor.fetchone()

    # If the worker exists, format and pass the data
    if result:
        context = {
            'worker_name': result[1],
            'worker_pic': result[2],
            'worker_rate': result[3],
            'worker_finished_orders': result[4],
            'worker_phone': result[5],
            'worker_dob': result[6],
            'worker_address': result[7],
        }
    else:
        context = {
            'error_message': 'Worker not found',
        }

    # Return the rendered template with the data
    return render(request, 'worker_profile.html', context)


def add_testimonial(request):
    context = {
        'rating_choices': range(1, 11) 
    }
    return render(request, 'add_testimonial.html', context)


from django.shortcuts import render, redirect
from django.db import connection
import uuid
from django.utils.timezone import now

from django.shortcuts import render, redirect
from django.db import connection
from django.utils.timezone import now

def add_testimonial(request):
    if request.method == 'POST':
        # Retrieve form data
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        current_time = now()

        # Insert data into the database
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sijarta.TESTIMONI (servicetrid, date, text, rating)
                VALUES (
                    (SELECT Id FROM sijarta.TR_SERVICE_ORDER LIMIT 1 OFFSET %s), %s, %s, %s
                )
            """, [0, current_time, comment, rating])  # Replace 0 with the correct OFFSET as needed

        return redirect('subcategory_services_user', id=request.user.id)  # Adjust as needed
    else:
        return render(request, 'add_testimonial.html', {'rating_choices': range(1, 11)})



def submit_testimonial(request):
    if request.method == 'POST':
        # Ambil data dari form
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        servicetrid = request.POST.get('servicetrid')  # Pastikan `servicetrid` dikirim dari form
        current_time = now()

        # Masukkan data testimonial ke database
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO sijarta.testimoni (servicetrid, date, text, rating)
                VALUES (%s, %s, %s, %s)
            """, [servicetrid, current_time, comment, rating])


        # Redirect ke halaman yang sesuai setelah submit
        return redirect('subcategory_services_user', id=servicetrid)
    else:
        # Redirect ke form testimonial jika bukan POST
        return redirect('add_testimonial')
