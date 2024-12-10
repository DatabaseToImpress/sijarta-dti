from datetime import datetime, timedelta
import uuid
import json
from django.db import connection, transaction
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

def get_user_balance(phone_number):
    with connection.cursor() as cursor:
        query = "SELECT MyPayBalance FROM sijarta.APP_USER WHERE PhoneNum = %s;"
        cursor.execute(query, [phone_number])
        result = cursor.fetchone()
    return result[0] if result else None

def get_transaction_history(phone_number):
    with connection.cursor() as cursor:
        query = """
            SELECT tr.Date, tr.Nominal, cat.Name AS Category 
            FROM sijarta.tr_mypay AS tr
            JOIN sijarta.tr_mypay_category AS cat ON tr.CategoryId = cat.Id 
            WHERE tr.UserId = (SELECT Id FROM sijarta.app_user WHERE PhoneNum = %s)
            ORDER BY tr.Date DESC;
        """
        cursor.execute(query, [phone_number])
        results = cursor.fetchall()
    return results

def mypay_view(request):
    if not request.session.get('user'):
        return redirect('login')

    user_data = json.loads(request.session.get('user'))
    phone_number = user_data.get('PhoneNum')
    user_name = user_data.get('Name')
    role = request.session.get('role')

    balance = get_user_balance(phone_number)
    transactions = get_transaction_history(phone_number)

    context = {
        'balance': balance,
        'transactions': transactions,
        'is_worker': role == 'Worker',
        'user_name': user_name,
        'phone_number': phone_number
    }
    return render(request, 'mypay.html', context)

@csrf_exempt
def mypay_transaction(request):
    user_data = json.loads(request.session.get('user')) 
    phone_number = user_data.get('PhoneNum')
    user_name = user_data.get('Name')
    current_balance = get_user_balance(phone_number)
    role = request.session.get('role')
    user_id = request.session.get('user_id')
    transaction_data = {'banks': [], 'services': []}

    if not user_id:
        return redirect('login') 

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, name FROM SIJARTA.payment_method WHERE name != 'MyPay'")
            transaction_data['banks'] = cursor.fetchall()

            if role == 'Customer':
                cursor.execute("""
                    SELECT tso.id, sc.subcategoryname AS description, tso.totalprice, tso.session 
                    FROM SIJARTA.tr_service_order tso
                    JOIN SIJARTA.service_subcategory sc ON tso.servicecategoryid = sc.id
                    JOIN SIJARTA.payment_method pm ON tso.paymentmethodid = pm.id
                    WHERE tso.customerid = (
                        SELECT id 
                        FROM SIJARTA.customer 
                        WHERE id = (SELECT id FROM SIJARTA.app_user WHERE name = %s)
                    ) AND pm.name = 'MyPay' AND tso.id NOT IN (
                        SELECT servicetrid 
                        FROM SIJARTA.tr_order_status 
                        WHERE statusid = (
                            SELECT id 
                            FROM SIJARTA.order_status 
                            WHERE status = 'Order completed'
                        )
                    )
                """, [user_name])
                transaction_data['services'] = cursor.fetchall()

            if request.method == 'POST':
                category = request.POST.get('category')

                # Top-Up MyPay functionality
                if category == 'topup':
                    amount = request.POST.get('topup_amount')
                    if not amount:
                        return render(request, 'mypay_transaction.html', {'error': 'Amount is required!', 'data': transaction_data, 'role': role})
                    try:
                        amount = float(amount)
                        if amount <= 0:
                            raise ValueError
                    except ValueError:
                        return render(request, 'mypay_transaction.html', {'error': 'Invalid amount! Please enter a positive number.', 'data': transaction_data, 'role': role})

                    cursor.execute(
                        "UPDATE SIJARTA.app_user SET mypaybalance = mypaybalance + %s WHERE id = %s",
                        [amount, user_id]
                    )

                    cursor.execute("""
                        INSERT INTO SIJARTA.tr_mypay (id, userid, date, nominal, categoryid)
                        VALUES (%s, %s, %s, %s, 
                            (SELECT id FROM SIJARTA.tr_mypay_category WHERE name = 'Topup'))
                    """, [str(uuid.uuid4()), user_id, datetime.now(), amount])

                    connection.commit()

                    return render(request, 'mypay_transaction.html', {'success': f'Top-up successful! Your balance has been increased by {amount}.', 'data': transaction_data, 'role': role})
                
                #Service Payment
                elif category == 'service_payment':
                    if role != 'Customer':
                        return render(request, 'mypay_transaction.html', {'error': 'Only customers can perform service payments!', 'data': transaction_data, 'role': role})

                    service_id = request.POST.get('session')
                    if not service_id:
                        return render(request, 'mypay_transaction.html', {'error': 'Please select a service!', 'data': transaction_data, 'role': role})

                    cursor.execute("""
                        SELECT tso.totalprice 
                        FROM SIJARTA.tr_service_order tso
                        JOIN SIJARTA.payment_method pm ON tso.paymentmethodid = pm.id
                        WHERE tso.id = %s AND tso.customerid = %s AND pm.name = 'MyPay'
                    """, [service_id, user_id])
                    
                    service_price = cursor.fetchone()
                    if not service_price:
                        return render(request, 'mypay_transaction.html', {'error': 'Service not found or already paid with another payment method!', 'data': transaction_data, 'role': role})

                    if current_balance < service_price[0]:
                        return render(request, 'mypay_transaction.html', {'error': 'Insufficient balance to pay for the service!', 'data': transaction_data, 'role': role})

                    cursor.execute(
                        "UPDATE SIJARTA.app_user SET mypaybalance = mypaybalance - %s WHERE id = %s",
                        [service_price[0], user_id]
                    )

                    cursor.execute("""
                        INSERT INTO SIJARTA.tr_mypay (id, userid, date, nominal, categoryid)
                        VALUES (%s, %s, %s, -%s, 
                            (SELECT id FROM SIJARTA.tr_mypay_category WHERE name = 'Pay for service transaction'))
                    """, [str(uuid.uuid4()), user_id, datetime.now(), service_price[0]])

                    cursor.execute("""
                        INSERT INTO SIJARTA.tr_order_status (servicetrid, statusid, date)
                        VALUES (%s, 
                            (SELECT id FROM SIJARTA.order_status WHERE status = 'Searching for Nearby Workers'), %s)
                    """, [service_id, datetime.now()])

                    connection.commit()

                    return render(request, 'mypay_transaction.html', {
                        'success': f'Service payment of IDR {service_price[0]:,.0f} completed successfully!',
                        'data': transaction_data,
                        'role': role
                    })

                # Transfer MyPay functionality
                elif category == 'transfer':
                    recipient_phone = request.POST.get('recipient_phone')
                    transfer_amount = request.POST.get('transfer_amount')
                    

                    if not recipient_phone or not transfer_amount:
                        return render(request, 'mypay_transaction.html', {'error': 'Both recipient and amount are required!', 'data': transaction_data, 'role': role})
                    
                    try:
                        transfer_amount = float(transfer_amount)
                        if transfer_amount <= 0:
                            raise ValueError
                    except ValueError:
                        return render(request, 'mypay_transaction.html', {'error': 'Invalid amount! Please enter a positive number.', 'data': transaction_data, 'role': role})

                    if current_balance < transfer_amount:
                        return render(request, 'mypay_transaction.html', {'error': 'Insufficient balance to complete the transfer!', 'data': transaction_data, 'role': role})

                    cursor.execute("SELECT id FROM SIJARTA.app_user WHERE phonenum = %s", [recipient_phone])
                    recipient = cursor.fetchone()
                    if not recipient:
                        print(f"Recipient with phone number {recipient_phone} not found.")
                        return render(request, 'mypay_transaction.html', {'error': 'Recipient not found!', 'data': transaction_data, 'role': role})

                    recipient_id = recipient[0]
                    print(f"Recipient ID: {recipient_id}")

                    cursor.execute(
                        "UPDATE SIJARTA.app_user SET mypaybalance = mypaybalance - %s WHERE id = %s",
                        [transfer_amount, user_id]
                    )
                    print("Sender balance updated")

                    cursor.execute(
                        "UPDATE SIJARTA.app_user SET mypaybalance = mypaybalance + %s WHERE id = %s",
                        [transfer_amount, recipient_id]
                    )
                    print("Recipient balance updated")

                    cursor.execute("""
                        INSERT INTO SIJARTA.tr_mypay (id, userid, date, nominal, categoryid)
                        VALUES (%s, %s, %s, -%s, 
                            (SELECT id FROM SIJARTA.tr_mypay_category WHERE name = 'Transfer MyPay to another user'))
                    """, [str(uuid.uuid4()), user_id, datetime.now(), transfer_amount])

                    cursor.execute("""
                        INSERT INTO SIJARTA.tr_mypay (id, userid, date, nominal, categoryid)
                        VALUES (%s, %s, %s, %s, 
                            (SELECT id FROM SIJARTA.tr_mypay_category WHERE name = 'Receive MyPay Transfer'))
                    """, [str(uuid.uuid4()), recipient_id, datetime.now(), transfer_amount])

                    connection.commit()

                    return render(request, 'mypay_transaction.html', {
                        'success': f'Transfer of IDR {transfer_amount:,.0f} to {recipient_phone} completed successfully!',
                        'data': transaction_data,
                        'role': role
                    })
                
                #Withdrawal
                elif category == 'withdrawal':
                    bank_id = request.POST.get('bank_name')
                    account_number = request.POST.get('bank_account')
                    withdrawal_amount = request.POST.get('amount')

                    if not bank_id or not account_number or not withdrawal_amount:
                        return render(request, 'mypay_transaction.html', {
                            'error': 'All fields are required for withdrawal!',
                            'data': transaction_data,
                        })

                    try:
                        withdrawal_amount = float(withdrawal_amount)
                        if withdrawal_amount <= 0:
                            raise ValueError
                    except ValueError:
                        return render(request, 'mypay_transaction.html', {
                            'error': 'Invalid amount! Please enter a positive number.',
                            'data': transaction_data,
                        })

                    if current_balance < withdrawal_amount:
                        return render(request, 'mypay_transaction.html', {
                            'error': 'Insufficient balance to withdraw the requested amount!',
                            'data': transaction_data,
                        })

                    cursor.execute(
                        "UPDATE SIJARTA.app_user SET mypaybalance = mypaybalance - %s WHERE id = %s",
                        [withdrawal_amount, user_id]
                    )

                    cursor.execute("""
                        INSERT INTO SIJARTA.tr_mypay (id, userid, date, nominal, categoryid)
                        VALUES (%s, %s, %s, -%s, 
                            (SELECT id FROM SIJARTA.tr_mypay_category WHERE name = 'Withdrawal MyPay to bank account'))
                    """, [str(uuid.uuid4()), user_id, datetime.now(), withdrawal_amount])

                    connection.commit()

                    return render(request, 'mypay_transaction.html', {
                        'success': f'Withdrawal of IDR {withdrawal_amount:,.0f} completed successfully!',
                        'data': transaction_data,
                    })        

        return render(request, 'mypay_transaction.html', {'data': transaction_data, 'role': role, 'transaction_date': datetime.now().strftime('%Y-%m-%d'),'mypay_balance': current_balance})
    except Exception as e:
        print(f"Error encountered: {e}")
        return render(request, 'mypay_transaction.html', {'error': f'An error occurred: {e}', 'data': transaction_data, 'role': role, 'transaction_date': datetime.now().strftime('%Y-%m-%d'),'mypay_balance': current_balance})

def service_job_status(request):
    """
    View for workers to manage the status of their service jobs.
    Allows filtering by service name (subcategoryname) or status.
    """
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    status_filter = request.GET.get('status', '').strip()
    service_name_filter = request.GET.get('order_name', '').strip()

    try:
        with connection.cursor() as cursor:
            query_conditions = [
                "tso.workerid = %s",
                "os.status NOT IN ('Waiting for Payment', 'Searching for Nearby Workers', 'Waiting for Nearby Worker')"
            ]
            query_params = [user_id]

            if status_filter:
                query_conditions.append("os.status = %s")
                query_params.append(status_filter)

            if service_name_filter:
                query_conditions.append("LOWER(ssc.subcategoryname) LIKE %s")
                query_params.append(f"%{service_name_filter.lower()}%")

            query = f"""
                SELECT 
                    ssc.subcategoryname AS service_subcategory_name,
                    au.name AS customer_name,
                    tso.orderdate AS order_date,
                    tso.session AS session,
                    tso.totalprice AS total_amount,
                    os.status AS current_status,
                    tso.id AS order_id
                FROM SIJARTA.tr_service_order tso
                JOIN SIJARTA.service_subcategory ssc ON tso.servicecategoryid = ssc.id
                JOIN SIJARTA.app_user au ON tso.customerid = au.id
                JOIN SIJARTA.tr_order_status tos ON tso.id = tos.servicetrid
                JOIN SIJARTA.order_status os ON tos.statusid = os.id
                WHERE {' AND '.join(query_conditions)}
                  AND tos.date = (
                    SELECT MAX(t2.date)
                    FROM SIJARTA.tr_order_status t2
                    WHERE t2.servicetrid = tso.id
                  )
                ORDER BY tso.orderdate DESC, tso.servicetime DESC
            """

            cursor.execute(query, query_params)
            orders = cursor.fetchall()

        formatted_orders = [
            {
                "service_subcategory_name": row[0],
                "customer_name": row[1],
                "order_date": row[2],
                "session": row[3],
                "total_amount": row[4],
                "current_status": row[5],
                "id": row[6] 
            }
            for row in orders
        ]

        return render(request, 'servicejob_status.html', {
            'orders': formatted_orders,
            'status_filter': status_filter,
            'service_name_filter': service_name_filter,
        })

    except Exception as e:
        print(f"Error fetching service job statuses: {e}")
        messages.error(request, "An error occurred while fetching service jobs.")
        return redirect('service_job_status')
    
@csrf_exempt
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)

        user_id = request.session.get('user_id')
        order_id = data.get('order_id')
        new_status = data.get('new_status')

        if not user_id:
            return JsonResponse({'success': False, 'error': 'User not logged in.'}, status=401)

        if not order_id or not new_status:
            return JsonResponse({'success': False, 'error': 'Missing order_id or new_status.'}, status=400)

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT os.status
                    FROM SIJARTA.tr_service_order tso
                    JOIN SIJARTA.tr_order_status tos ON tso.id = tos.servicetrid
                    JOIN SIJARTA.order_status os ON tos.statusid = os.id
                    WHERE tso.id = %s
                    ORDER BY tos.date DESC
                    LIMIT 1
                """, [order_id])
                current_status_row = cursor.fetchone()

                if not current_status_row:
                    return JsonResponse({'success': False, 'error': 'Order not found.'}, status=404)

                current_status = current_status_row[0]

                status_transitions = {
                    "Waiting for Worker to Depart": "Worker arrives at the location",
                    "Worker arrives at the location": "Service is being performed",
                    "Service is being performed": "Order completed"
                }

                if current_status not in status_transitions or status_transitions[current_status] != new_status:
                    return JsonResponse({'success': False, 'error': 'Invalid status transition.'}, status=400)

                cursor.execute("""
                    INSERT INTO SIJARTA.tr_order_status (servicetrid, statusid, date)
                    VALUES (
                        %s,
                        (SELECT id FROM SIJARTA.order_status WHERE status = %s),
                        CURRENT_TIMESTAMP
                    )
                """, [order_id, new_status])

                connection.commit()

            return JsonResponse({'success': True})
        except Exception as e:
            print(f"Error updating order status: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

def service_job(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT sc.id, sc.categoryname
            FROM SIJARTA.worker_service_category wsc
            JOIN SIJARTA.service_category sc ON wsc.servicecategoryid = sc.id
            WHERE wsc.workerid = %s
        """, [user_id])
        worker_categories = cursor.fetchall()
    formatted_categories = [{"id": str(row[0]), "name": row[1]} for row in worker_categories]

    category_filter = request.GET.get('category_id', '').strip()
    subcategory_filter = request.GET.get('subcategory_id', '').strip()


    formatted_subcategories = []
    with connection.cursor() as cursor:
        if category_filter:
            cursor.execute("""
                SELECT ssc.id, ssc.subcategoryname
                FROM SIJARTA.service_subcategory ssc
                WHERE ssc.servicecategoryid = %s
            """, [category_filter])
        else:
            if worker_categories:
                category_ids = [cat["id"] for cat in formatted_categories]
                placeholders = ",".join(["%s"] * len(category_ids))
                cursor.execute(f"""
                    SELECT ssc.id, ssc.subcategoryname
                    FROM SIJARTA.service_subcategory ssc
                    WHERE ssc.servicecategoryid IN ({placeholders})
                """, category_ids)
            else:
                cursor.execute("SELECT id, subcategoryname FROM SIJARTA.service_subcategory WHERE 1=0") # returns empty
        subcategories = cursor.fetchall()
        formatted_subcategories = [{"id": str(row[0]), "name": row[1]} for row in subcategories]

    query_conditions = [
        "os.status = 'Searching for Nearby Workers'",
        """tos.date = (
            SELECT MAX(t2.date)
            FROM SIJARTA.tr_order_status t2
            WHERE t2.servicetrid = tso.id
        )"""
    ]
    query_params = []

    if worker_categories:
        worker_category_ids = [cat["id"] for cat in formatted_categories]
        if category_filter:
            query_conditions.append("sc.id = %s")
            query_params.append(category_filter)

            if subcategory_filter:
                query_conditions.append("ssc.id = %s")
                query_params.append(subcategory_filter)
            else:
                pass
        else:
            placeholders = ",".join(["%s"] * len(worker_category_ids))
            query_conditions.append(f"sc.id IN ({placeholders})")
            query_params.extend(worker_category_ids)
    else:
        query_conditions.append("1=0")

    with connection.cursor() as cursor:
        query = f"""
            SELECT 
                sc.id AS category_id,
                sc.categoryname,
                ssc.id AS subcategory_id,
                ssc.subcategoryname,
                au.name AS customer_name,
                tso.id AS order_id,
                tso.orderdate,
                tso.session,
                tso.totalprice,
                os.status
            FROM SIJARTA.tr_service_order tso
            JOIN SIJARTA.service_session ss ON tso.servicecategoryid = ss.subcategoryid AND tso.session = ss.session
            JOIN SIJARTA.service_subcategory ssc ON ss.subcategoryid = ssc.id
            JOIN SIJARTA.service_category sc ON ssc.servicecategoryid = sc.id
            JOIN SIJARTA.app_user au ON tso.customerid = au.id
            JOIN SIJARTA.tr_order_status tos ON tso.id = tos.servicetrid
            JOIN SIJARTA.order_status os ON tos.statusid = os.id
            WHERE {' AND '.join(query_conditions)}
            ORDER BY tso.orderdate DESC
        """
        cursor.execute(query, query_params)
        orders = cursor.fetchall()

    formatted_orders = [
        {
            "category_id": str(row[0]),
            "category_name": row[1],
            "subcategory_id": str(row[2]),
            "service_subcategory_name": row[3],
            "customer_name": row[4],
            "id": str(row[5]),
            "order_date": row[6],
            "session": row[7],
            "total_amount": row[8],
            "current_status": row[9]
        }
        for row in orders
    ]

    return render(request, 'servicejob.html', {
        'orders': formatted_orders,
        'categories': formatted_categories,
        'selected_category': category_filter,
        'subcategories': formatted_subcategories,
        'selected_subcategory': subcategory_filter
    })


@csrf_exempt
def accept_order(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'success': False, 'error': 'Invalid request data.'}, status=400)

    # Get the worker's ID from the session
    user_id = request.session.get('user_id')
    if not user_id:
        return JsonResponse({'success': False, 'error': 'User not logged in.'}, status=401)

    if not order_id:
        return JsonResponse({'success': False, 'error': 'Order ID is required.'}, status=400)

    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT os.status, tso.session
                    FROM SIJARTA.tr_service_order tso
                    JOIN SIJARTA.tr_order_status tos ON tso.id = tos.servicetrid
                    JOIN SIJARTA.order_status os ON tos.statusid = os.id
                    WHERE tso.id = %s
                    ORDER BY tos.date DESC
                    LIMIT 1
                """, [order_id])
                row = cursor.fetchone()

                if not row:
                    return JsonResponse({'success': False, 'error': 'Order not found.'}, status=404)

                current_status, session_duration = row

                if current_status != "Searching for Nearby Workers":
                    return JsonResponse({'success': False, 'error': 'Order is not available to take.'}, status=400)

                service_date = datetime.now().date()
                job_duration = service_date + timedelta(days=session_duration)

                cursor.execute("""
                    UPDATE SIJARTA.tr_service_order
                    SET workerid = %s, servicedate = %s
                    WHERE id = %s
                """, [user_id, service_date, order_id])

                cursor.execute("""
                    INSERT INTO SIJARTA.tr_order_status (servicetrid, statusid, date)
                    VALUES (
                        %s,
                        (SELECT id FROM SIJARTA.order_status WHERE status = 'Waiting for Worker to Depart'),
                        CURRENT_TIMESTAMP
                    )
                """, [order_id])

        return JsonResponse({
            'success': True,
            'message': 'Order accepted successfully.',
            'order_id': order_id,
            'worker_id': user_id,
            'service_date': service_date,
            'job_duration': job_duration
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': 'An error occurred while processing the order.'}, status=500)