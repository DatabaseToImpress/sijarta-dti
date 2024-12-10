from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
import json, uuid
from decimal import Decimal
from django.db import IntegrityError
from django.urls import reverse

def landing(request):
    return render(request, 'landing.html')

def login(request):
    if request.method == "POST":
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, sex, phonenum, pwd, dob, address, mypaybalance
                    FROM sijarta.app_user
                    WHERE phonenum = %s
                """, [phone_number])
                user = cursor.fetchone()

            if not user:
                messages.error(request, "Invalid phone number or password. Please try again.")
                return render(request, "login.html")

            hashed_password = user[4]  

            if password != hashed_password:  
                messages.error(request, "Invalid phone number or password. Please try again.")
                return render(request, "login.html")

            user_columns = ['Id', 'Name', 'Sex', 'PhoneNum', 'Pwd', 'DoB', 'Address', 'MyPayBalance']
            user_data = dict(zip(user_columns, user))

            user_data['Id'] = str(user_data['Id']) 
            user_data['DoB'] = user_data['DoB'].isoformat() if user_data['DoB'] else None
            user_data['MyPayBalance'] = float(user_data['MyPayBalance']) if user_data['MyPayBalance'] is not None else 0.0

            request.session['user'] = json.dumps(user_data)  
            request.session['user_id'] = user_data['Id']  
            request.session['user_name'] = user_data['Name']

            with connection.cursor() as cursor:
                cursor.execute("SELECT id FROM sijarta.customer WHERE id = %s", [user_data['Id']])
                customer = cursor.fetchone()

            if customer:
                request.session['role'] = 'Customer'
            else:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT id FROM sijarta.worker WHERE id = %s", [user_data['Id']])
                    worker = cursor.fetchone()

                if worker:
                    request.session['role'] = 'Worker'
                    request.session['worker_id'] = user_data['Id']
                else:
                    messages.error(request, "You do not have a valid role. Please contact support.")
                    return render(request, "login.html")

            return HttpResponseRedirect(reverse('main:home_page'))

        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return render(request, "login.html")

    return render(request, "login.html")


def register_landing(request):
    return render(request, 'register/register_landing.html')

def register_user(request):
    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        phone_number = request.POST.get('phone_number')
        dob = request.POST.get('birth_date')
        address = request.POST.get('address')

        if not (name and password and sex and phone_number and dob and address):
            messages.error(request, "All fields are required.")
            return render(request, "register/register_user.html")

        with connection.cursor() as cursor:
            try:
                    cursor.execute("""
                        SELECT * FROM sijarta.app_user WHERE phonenum = %s
                    """, [phone_number])
                    if cursor.fetchone():
                        messages.error(request, "Phone number already registered.")
                        return render(request, "register/register_user.html")

                    # Insert into APP_USER
                    user_id = str(uuid.uuid4())
                    cursor.execute("""
                        INSERT INTO sijarta.app_user (id, name, sex, phonenum, pwd, dob, address, mypaybalance)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, [user_id, name, sex, phone_number, password, dob, address, Decimal(0)])

                    # Insert into CUSTOMER
                    cursor.execute("""
                        INSERT INTO sijarta.customer (id, level)
                        VALUES (%s, %s)
                    """, [user_id, 'Basic'])

                    return redirect("login")

            except IntegrityError as e:
                error_message = str(e)
                messages.error(request, f"Error: {error_message}")
                return render(request, "register/register_user.html")

            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {str(e)}")
                return render(request, "register/register_user.html")

    return render(request, "register/register_user.html")

def register_worker(request):
    if request.method == "POST":
        name = request.POST.get('name')
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        phone_number = request.POST.get('phone_number')
        dob = request.POST.get('birth_date')
        address = request.POST.get('address')
        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')
        npwp = request.POST.get('npwp')
        pic_url = request.POST.get('image_url')

        if not (name and password and sex and phone_number and dob and address and bank_name and account_number and npwp and pic_url):
            messages.error(request, "All fields are required.")
            return render(request, "register/register_worker.html")

        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    SELECT * FROM sijarta.app_user WHERE phonenum = %s
                """, [phone_number])
                if cursor.fetchone():
                    messages.error(request, "Phone number already registered.")
                    return render(request, "register/register_worker.html")

                user_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sijarta.app_user (id, name, sex, phonenum, pwd, dob, address, mypaybalance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [user_id, name, sex, phone_number, password, dob, address, Decimal(0)])

                cursor.execute("""
                    INSERT INTO sijarta.worker (id, bankname, accnumber, npwp, picurl, rate, totalfinishorder)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [user_id, bank_name, account_number, npwp, pic_url, 0.0, 0])

                return redirect("login")

            except IntegrityError as e:
                error_message = str(e)
                messages.error(request, f"Error: {error_message}")
                return render(request, "register/register_worker.html")
            except Exception as e:
                messages.error(request, f"An unexpected error occurred: {str(e)}")
                return render(request, "register/register_worker.html")

    return render(request, "register/register_worker.html")

def logout(request):
    request.session.flush()
    return redirect('landing')

def profileu(request):
    user_id = request.session.get('user_id')  
    if not user_id:
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Name, Sex, PhoneNum, DoB, Address, MyPayBalance, Level
            FROM sijarta.app_user
            INNER JOIN sijarta.customer ON sijarta.app_user.Id = sijarta.customer.Id
            WHERE sijarta.app_user.Id = %s
        """, [user_id])
        user_data = cursor.fetchone()

    if not user_data:
        return redirect('login')

    user_data_dict = {
        "name": user_data[0],
        "sex": user_data[1],
        "phone_number": user_data[2],
        "dob": user_data[3],
        "address": user_data[4],
        "my_pay_balance": user_data[5],
        "level": user_data[6],
    }

    return render(request, 'profile/profile_user.html', {'user_data': user_data_dict})

def profileUserUpdate(request):
    if request.method == "POST":
        user_id = request.session.get('user_id')
        name = request.POST.get('name')
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        phone_number = request.POST.get('phone_number')
        dob = request.POST.get('birth_date')
        address = request.POST.get('address')

        if not (name and sex and phone_number and dob and address):
            messages.error(request, "All fields except password are required.")
            return redirect('profileUserUpdate')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sijarta.app_user
                    SET Name = %s, Sex = %s, PhoneNum = %s, DoB = %s, Address = %s
                    WHERE Id = %s
                """, [name, sex, phone_number, dob, address, user_id])

                if password:
                    cursor.execute("""
                        UPDATE sijarta.app_user
                        SET Pwd = %s
                        WHERE Id = %s
                    """, [password, user_id])

            request.session['user_name'] = name
            return redirect('profileu')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('profileUserUpdate')

    user_id = request.session.get('user_id')
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Name, Sex, PhoneNum, DoB, Address
            FROM sijarta.app_user
            WHERE Id = %s
        """, [user_id])
        user_data = cursor.fetchone()

    user_data_dict = {
        "name": user_data[0],
        "sex": user_data[1],
        "phone_number": user_data[2],
        "dob": user_data[3],
        "address": user_data[4],
    }

    return render(request, 'profile/profileUser_update.html', {'user_data': user_data_dict})

def profilew(request):
    worker_id = request.session.get('worker_id')  
    if not worker_id:
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Name, Sex, PhoneNum, DoB, Address, MyPayBalance, BankName, AccNumber, NPWP, PicURL, Rate, TotalFinishOrder
            FROM sijarta.app_user
            INNER JOIN sijarta.worker ON sijarta.app_user.Id = sijarta.worker.Id
            WHERE sijarta.app_user.Id = %s
        """, [worker_id])
        worker_data = cursor.fetchone()

        cursor.execute("""
            SELECT sc.CategoryName
            FROM sijarta.worker_service_category wsc
            JOIN sijarta.service_category sc ON wsc.ServiceCategoryId = sc.Id
            WHERE wsc.WorkerId = %s
        """, [worker_id])
        job_categories = cursor.fetchall() 
    if not worker_data:
        return redirect('login')

    worker_data_dict = {
        "name": worker_data[0],
        "sex": worker_data[1],
        "phone_number": worker_data[2],
        "dob": worker_data[3],
        "address": worker_data[4],
        "my_pay_balance": worker_data[5],
        "bank_name": worker_data[6],
        "account_number": worker_data[7],
        "npwp": worker_data[8],
        "pic_url": worker_data[9],
        "rate": worker_data[10],
        "completed_orders": worker_data[11],
        "job_categories": [category[0] for category in job_categories],  
    }

    return render(request, 'profile/profile_worker.html', {'worker_data': worker_data_dict})

def profileWorkerUpdate(request):
    if request.method == "POST":
        worker_id = request.session.get('worker_id')
        name = request.POST.get('name')
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        phone_number = request.POST.get('phone_number')
        dob = request.POST.get('birth_date')
        address = request.POST.get('address')
        bank_name = request.POST.get('bank_name')
        account_number = request.POST.get('account_number')
        npwp = request.POST.get('npwp')
        pic_url = request.POST.get('image_url')

        if not (name and sex and phone_number and dob and address and bank_name and account_number and npwp and pic_url):
            messages.error(request, "All fields except password are required.")
            return redirect('profileWorkerUpdate')

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sijarta.app_user
                    SET Name = %s, Sex = %s, PhoneNum = %s, DoB = %s, Address = %s
                    WHERE Id = %s
                """, [name, sex, phone_number, dob, address, worker_id])

                if password:
                    cursor.execute("""
                        UPDATE sijarta.app_user
                        SET Pwd = %s
                        WHERE Id = %s
                    """, [password, worker_id])

                cursor.execute("""
                    UPDATE sijarta.worker
                    SET BankName = %s, AccNumber = %s, NPWP = %s, PicURL = %s
                    WHERE Id = %s
                """, [bank_name, account_number, npwp, pic_url, worker_id])

            request.session['user_name'] = name

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")  

        return redirect('profilew')

    return render(request, 'profile/profileWorker_update.html')