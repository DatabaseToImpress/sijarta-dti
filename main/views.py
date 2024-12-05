from django.db import connection
from django.shortcuts import render
from collections import defaultdict


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
    
    # Query to fetch subcategory and service category details
    subcategory_query = """
        SELECT
            ssc.SubcategoryName, 
            ssc.Description,
            sc.CategoryName
        FROM sijarta.SERVICE_SUBCATEGORY ssc
        JOIN sijarta.SERVICE_CATEGORY sc ON ssc.ServiceCategoryId = sc.Id
        WHERE ssc.Id = %s
    """
    
    # Query to fetch available workers
    workers_query = """
        SELECT DISTINCT au.Name
        FROM sijarta.WORKER_SERVICE_CATEGORY wsc
        JOIN sijarta.WORKER w ON w.Id = wsc.WorkerId
        JOIN sijarta.SERVICE_CATEGORY sc ON sc.Id = wsc.ServiceCategoryId
        JOIN sijarta.APP_USER au ON au.Id = w.Id
        WHERE sc.Id = (SELECT ServiceCategoryId FROM sijarta.SERVICE_SUBCATEGORY WHERE Id = %s)
    """

    # Query to fetch service sessions and prices for the selected subcategory
    sessions_query = """
        SELECT Session, Price
        FROM sijarta.SERVICE_SESSION
        WHERE SubcategoryId = %s
    """

    with connection.cursor() as cursor:
        # Fetch subcategory details
        cursor.execute(subcategory_query, [id])
        subcategory_result = cursor.fetchall()

        # Fetch distinct worker names
        cursor.execute(workers_query, [id])
        workers_result = cursor.fetchall()

        # Fetch service sessions and prices
        cursor.execute(sessions_query, [id])
        sessions_result = cursor.fetchall()

    # Prepare subcategory data
    subcategory_data = {
        'subcategory_name': subcategory_result[0][0],
        'description': subcategory_result[0][1],
        'service_category': subcategory_result[0][2],
    }

    # Extract worker names and remove duplicates
    workers = list(set(worker[0] for worker in workers_result))  # `set` ensures no duplicates

    # Prepare sessions data
    sessions = [{'session': session[0], 'price': session[1]} for session in sessions_result]

    # Add data to context
    context = {
        'category': category,
        'subcategory': subcategory,
        'id': id,
        'subcategory_data': subcategory_data,
        'workers': workers,  # Pass distinct workers
        'sessions': sessions,  # Pass service sessions
    }

    # Render the template
    return render(request, 'subcategory_services_user.html', context)


def booking_view(request):
    return render(request, "booking.html")

def worker_profile(request, worker_name):
    context = {
        'worker_name': worker_name,
    }
    return render(request, 'worker_profile.html', context)

def subcategory_services_worker(request, id):
    category = request.GET.get('category', None)
    subcategory = request.GET.get('subcategory', None)
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'id': id,  # Add id to context so you can use it in the template
    }
    return render(request, 'subcategory_services_worker.html', context)

def add_testimonial(request):
    context = {
        'rating_choices': range(1, 11) 
    }
    return render(request, 'add_testimonial.html', context)


def submit_testimonial(request):
    if request.method == 'POST':

        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        print(f"Rating: {rating}, Comment: {comment}")

        return redirect('add_testimonial')  
    else:

        return redirect('add_testimonial')

def subcategory_services_worker(request, id):
    category = request.GET.get('category', None)
    subcategory = request.GET.get('subcategory', None)
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'id': id,
    }
    return render(request, 'subcategory_services_worker.html', context)
