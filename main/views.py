from django.shortcuts import render, redirect

# Example view for HomePage
def home_page(request):
    return render(request, 'home.html')

def subcategory_services_user(request, id):
    category = request.GET.get('category', None)
    subcategory = request.GET.get('subcategory', None)
    
    context = {
        'category': category,
        'subcategory': subcategory,
        'id': id,  # Add id to context so you can use it in the template
    }
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
