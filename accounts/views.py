from django.shortcuts import render, redirect

def landing(request):
    return render(request, 'landing.html')

def register(request):
    return render(request, 'register.html')

def login(request):
    return render(request, 'login.html')

def logout(request):
    return redirect('landing')

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

def profileu(request):
    if request.method == 'POST':
        # Handle profile updates
        user = request.user
        user.name = request.POST.get('name')
        user.password = request.POST.get('password') or user.password
        user.sex = request.POST.get('sex')
        user.phone = request.POST.get('phone')
        user.birth_date = request.POST.get('birth_date')
        user.address = request.POST.get('address')
        user.save()
        return redirect('profileu')
    return render(request, 'profile/profile_user.html')

def profilew(request):
    #if not request.user.is_authenticated:
        #return redirect('login')
    if request.method == 'POST':
        pass
        return redirect('profilew')
    return render(request, 'profile/profile_worker.html')

def profileUserUpdate(request):
    return render(request, 'profile/profileUser_update.html')

def profileWorkerUpdate(request):
    return render(request, 'profile/profileWorker_update.html')