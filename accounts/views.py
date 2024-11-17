from django.shortcuts import render, redirect

def landing(request):
    return render(request, 'landing.html')

def register(request):
    return render(request, 'register.html')

def login(request):
    return render(request, 'login.html')

def logout(request):
    return render(request, 'logout.html')

def register_landing(request):
    return render(request, 'register/register_landing.html')

def register_user(request):
    if request.method == 'POST':
        # Handle user registration logic here
        pass
    return render(request, 'register/register_user.html')

def register_worker(request):
    if request.method == 'POST':
        # Handle worker registration logic here
        pass
    return render(request, 'register/register_worker.html')

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.method == 'POST':
        # Handle profile updates
        user = request.user
        user.name = request.POST.get('name')
        user.password = request.POST.get('password') or user.password
        user.sex = request.POST.get('sex')
        user.phone = request.POST.get('phone')
        user.birth_date = request.POST.get('birth_date')
        user.address = request.POST.get('address')
        if user.role == 'Worker':
            user.bank_name = request.POST.get('bank_name')
            user.account_number = request.POST.get('account_number')
            user.npwp = request.POST.get('npwp')
            user.image_url = request.POST.get('image_url')
        user.save()
        return redirect('profile')
    return render(request, 'profile.html')