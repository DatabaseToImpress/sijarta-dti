from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.db import connection
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
import json, datetime, uuid
from decimal import Decimal
from django.db import IntegrityError
from django.urls import reverse
# from django.utils.dateparse import parse_date 

def landing(request):
    return render(request, 'landing.html')

def login(request):
    if request.method == "POST":
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')

        print("Login attempt with phone_number:", phone_number)  # Debugging print

        try:
            with connection.cursor() as cursor:
                # Explicitly refer to schema and table names
                cursor.execute("""
                    SELECT id FROM sijarta.app_user
                    WHERE phonenum = %s AND pwd = %s
                """, [phone_number, password])
                user = cursor.fetchone()
                user_id = str(user[0])

            print("User data fetched:", user)  # Debugging print

            if not user:
                # If no matching user is found, display an error message
                messages.error(request, "Invalid phone number or password. Please try again.")
                print("Login failed: No user found with provided credentials.")  # Debugging print
                return render(request, "login.html")

            # # Save user data to session
            # user_columns = ['Id', 'Name', 'Sex', 'PhoneNum', 'Pwd', 'DoB', 'Address', 'MyPayBalance']
            # user_data = dict(zip(user_columns, user))

            # # Convert UUID to string, DoB to ISO string format, and MyPayBalance (Decimal) to float for JSON serialization
            # user_data['Id'] = str(user_data['Id'])
            # if isinstance(user_data['DoB'], (datetime.date, datetime.datetime)):
            #     user_data['DoB'] = user_data['DoB'].isoformat()
            # if isinstance(user_data['MyPayBalance'], Decimal):
            #     user_data['MyPayBalance'] = float(user_data['MyPayBalance'])

            # request.session['user'] = json.dumps(user_data)
            
            user_data = []
            # Check if the user is a CUSTOMER
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM sijarta.app_user WHERE id = %s
                """, [user_id])
                role = cursor.fetchone()

            if role:
                # Save customer-specific data to session
                request.session['role'] = 'Customer'
            else:
                # Check if the user is a WORKER
                request.session['role'] = 'Worker'
                # with connection.cursor() as cursor:
                #     cursor.execute("""
                #         SELECT * FROM "WORKER" WHERE "Id" = %s
                #     """, [user_data['Id']])
                #     worker = cursor.fetchone()

                # print("Worker data fetched:", worker)  # Debugging print

                # if worker:
                #     # Save worker-specific data to session
                #     worker_columns = ['Id', 'BankName', 'AccNumber', 'NPWP', 'PicURL', 'Rate', 'TotalFinishOrder']
                #     worker_data = dict(zip(worker_columns, worker))

                #     # Convert UUID to string for JSON serialization
                #     worker_data['Id'] = str(worker_data['Id'])

                #     request.session['role'] = 'Worker'
                #     request.session['worker'] = json.dumps(worker_data)
                # else:
                #     # If neither CUSTOMER nor WORKER, assign as general APP_USER
                #     request.session['role'] = 'General User'

            # Redirect to the appropriate homepage/dashboard
            print("Redirecting to home_page.")  # Debugging print
            return HttpResponseRedirect(reverse('main:home_page'))

        except Exception as e:
            # Handle unexpected errors
            print("Error during login process:", str(e))  # Debugging print
            messages.error(request, "An unexpected error occurred. Please try again.")
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
                    # Ensure Phone Number uniqueness
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

                    messages.success(request, "User registration successful!")
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
                # Ensure Phone Number and NPWP uniqueness
                cursor.execute("""
                    SELECT * FROM sijarta.app_user WHERE phonenum = %s
                """, [phone_number])
                if cursor.fetchone():
                    messages.error(request, "Phone number already registered.")
                    return render(request, "register/register_worker.html")

                # Insert into APP_USER
                user_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO sijarta.app_user (id, name, sex, phonenum, pwd, dob, address, mypaybalance)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [user_id, name, sex, phone_number, password, dob, address, Decimal(0)])

                # Insert into WORKER
                cursor.execute("""
                    INSERT INTO sijarta.worker (id, bankname, accnumber, npwp, picurl, rate, totalfinishorder)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, [user_id, bank_name, account_number, npwp, pic_url, 0.0, 0])

                messages.success(request, "Worker registration successful!")
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
    user_id = request.session.get('user_id')  # Assuming you store user_id in session
    if not user_id:
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Name, Sex, PhoneNum, DoB, Address, MyPayBalance, Level
            FROM APP_USER
            INNER JOIN CUSTOMER ON APP_USER.Id = CUSTOMER.Id
            WHERE APP_USER.Id = %s
        """, [user_id])
        user_data = cursor.fetchone()

    if not user_data:
        return redirect('login')

    context = {
        "name": user_data[0],
        "sex": user_data[1],
        "phone_number": user_data[2],
        "birth_date": user_data[3],
        "address": user_data[4],
        "mypay_balance": user_data[5],
        "level": user_data[6],
    }
    return render(request, 'profile/profile_user.html', context)

def profileUserUpdate(request):
    if request.method == "POST":
        user_id = request.session.get('user_id')  # Assuming you store user_id in session
        name = request.POST.get('name')
        password = request.POST.get('password')
        sex = request.POST.get('sex')
        phone_number = request.POST.get('phone_number')
        dob = request.POST.get('birth_date')
        address = request.POST.get('address')

        if not (name and sex and phone_number and dob and address):
            messages.error(request, "All fields except password are required.")
            return redirect('profileUserUpdate')

        hashed_password = make_password(password) if password else None

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE APP_USER
                SET Name = %s, Sex = %s, PhoneNum = %s, DoB = %s, Address = %s
                WHERE Id = %s
            """, [name, sex, phone_number, dob, address, user_id])

            if hashed_password:
                cursor.execute("""
                    UPDATE APP_USER
                    SET Pwd = %s
                    WHERE Id = %s
                """, [hashed_password, user_id])

        messages.success(request, "Profile updated successfully!")
        return redirect('profileu')

    return render(request, 'profile/profileUser_update.html')

def profilew(request):
    worker_id = request.session.get('worker_id')  # Assuming you store worker_id in session
    if not worker_id:
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Name, Sex, PhoneNum, DoB, Address, MyPayBalance, BankName, AccNumber, NPWP, PicURL, Rate, TotalFinishOrder
            FROM APP_USER
            INNER JOIN WORKER ON APP_USER.Id = WORKER.Id
            WHERE APP_USER.Id = %s
        """, [worker_id])
        worker_data = cursor.fetchone()

    if not worker_data:
        return redirect('login')

    context = {
        "name": worker_data[0],
        "sex": worker_data[1],
        "phone_number": worker_data[2],
        "birth_date": worker_data[3],
        "address": worker_data[4],
        "mypay_balance": worker_data[5],
        "bank_name": worker_data[6],
        "account_number": worker_data[7],
        "npwp": worker_data[8],
        "pic_url": worker_data[9],
        "rate": worker_data[10],
        "completed_order_count": worker_data[11],
    }
    return render(request, 'profile/profile_worker.html', context)

def profileWorkerUpdate(request):
    if request.method == "POST":
        worker_id = request.session.get('worker_id')
        if not worker_id:
            messages.error(request, "You must be logged in to update your profile.")
            return redirect('login')

        # Get form data
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

        hashed_password = make_password(password) if password else None

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE APP_USER
                    SET Name = %s, Sex = %s, PhoneNum = %s, DoB = %s, Address = %s
                    WHERE Id = %s
                """, [name, sex, phone_number, dob, address, worker_id])

                if hashed_password:
                    cursor.execute("""
                        UPDATE APP_USER
                        SET Pwd = %s
                        WHERE Id = %s
                    """, [hashed_password, worker_id])

                cursor.execute("""
                    UPDATE WORKER
                    SET BankName = %s, AccNumber = %s, NPWP = %s, PicURL = %s
                    WHERE Id = %s
                """, [bank_name, account_number, npwp, pic_url, worker_id])

            messages.success(request, "Profile updated successfully!")
            return redirect('profilew')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('profileWorkerUpdate')

    # Fetch existing data for prefilling the form
    worker_id = request.session.get('worker_id')
    if not worker_id:
        messages.error(request, "You must be logged in to update your profile.")
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT Name, Sex, PhoneNum, DoB, Address, BankName, AccNumber, NPWP, PicURL
            FROM APP_USER
            INNER JOIN WORKER ON APP_USER.Id = WORKER.Id
            WHERE APP_USER.Id = %s
        """, [worker_id])
        worker_data = cursor.fetchone()

    context = {
        "worker_data": {
            "name": worker_data[0],
            "sex": worker_data[1],
            "phone_number": worker_data[2],
            "birth_date": worker_data[3],
            "address": worker_data[4],
            "bank_name": worker_data[5],
            "account_number": worker_data[6],
            "npwp": worker_data[7],
            "pic_url": worker_data[8],
        }
    }
    return render(request, 'profile/profileWorker_update.html', context)
