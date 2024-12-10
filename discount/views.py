from django.shortcuts import render
from django.db import connection  

from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.db import connection
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from uuid import uuid4


def discount_page(request):
    with connection.cursor() as cursor:
        # Fetch vouchers
        cursor.execute("""
            SELECT 
                d.Code, 
                d.Discount, 
                d.MinTrOrder, 
                v.NmbDayValid, 
                v.UserQuota, 
                v.Price
            FROM 
                sijarta.DISCOUNT d
            JOIN 
                sijarta.VOUCHER v ON d.Code = v.Code
        """)
        vouchers = cursor.fetchall()

        # Fetch promos
        cursor.execute("""
            SELECT 
                d.Code, 
                p.OfferEndDate
            FROM 
                sijarta.DISCOUNT d
            JOIN 
                sijarta.PROMO p ON d.Code = p.Code
        """)
        promos = cursor.fetchall()

        # Fetch payment methods
        cursor.execute("""
            SELECT id, name 
            FROM sijarta.PAYMENT_METHOD
        """)
        payment_methods = cursor.fetchall()

    context = {
        'vouchers': vouchers,
        'promos': promos,
        'payment_methods': payment_methods,
    }
    return render(request, 'discount.html', context)


@csrf_exempt
def buy_voucher(request):
    if request.method == 'POST':
        voucher_code = request.POST.get('voucher_code')
        payment_method = request.POST.get('payment_method')

        if not voucher_code or not payment_method:
            return JsonResponse({
                'success': False,
                'message': 'Voucher code or payment method is missing.',
            })

        with connection.cursor() as cursor:
            # Fetch voucher details
            cursor.execute("""
                SELECT v.NmbDayValid, v.UserQuota, v.Price
                FROM sijarta.VOUCHER v
                WHERE v.Code = %s
            """, [voucher_code])
            voucher = cursor.fetchone()

        if not voucher:
            return JsonResponse({
                'success': False,
                'message': 'Voucher not found.',
            })

        valid_days, user_quota, price = voucher

        # For non-MyPay transactions
        if payment_method != 'MyPay':
            add_transaction_to_voucher_payment(voucher_code, payment_method, valid_days, request.session.get('user_id'))
            return JsonResponse({
                'success': True,
                'message': f'Voucher {voucher_code} purchased successfully with {payment_method}!',
                'valid_until': (datetime.now() + timedelta(days=valid_days)).strftime('%d/%m/%Y'),
                'usage_quota': user_quota,
            })

        # For MyPay transactions
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User not authenticated. Please login first.',
            })

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT MyPayBalance
                FROM sijarta.APP_USER
                WHERE Id = %s
            """, [user_id])
            row = cursor.fetchone()

        if not row:
            return JsonResponse({
                'success': False,
                'message': 'User not found in the database.',
            })

        user_balance = float(row[0])

        if user_balance >= float(price):
            new_balance = user_balance - float(price)
            with connection.cursor() as cursor:
                # Update MyPay balance
                cursor.execute("""
                    UPDATE sijarta.APP_USER
                    SET MyPayBalance = %s
                    WHERE Id = %s
                """, [new_balance, user_id])

                # Add transaction to TR_VOUCHER_PAYMENT
                add_transaction_to_voucher_payment(voucher_code, payment_method, valid_days, user_id)

            return JsonResponse({
                'success': True,
                'message': f'Voucher {voucher_code} purchased successfully with MyPay!',
                'valid_until': (datetime.now() + timedelta(days=valid_days)).strftime('%d/%m/%Y'),
                'usage_quota': user_quota,
                'remaining_balance': new_balance,
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Sorry. Your balance is not enough to buy this voucher!',
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def add_transaction_to_voucher_payment(voucher_code, payment_method, valid_days, user_id):
    """Add a new transaction to the TR_VOUCHER_PAYMENT table."""
    with connection.cursor() as cursor:
        # Get payment method ID
        cursor.execute("""
            SELECT Id FROM sijarta.PAYMENT_METHOD
            WHERE Name = %s
        """, [payment_method])
        payment_method_id = cursor.fetchone()

        if not payment_method_id:
            raise ValueError("Invalid payment method!")

        # Insert into TR_VOUCHER_PAYMENT
        cursor.execute("""
            INSERT INTO sijarta.TR_VOUCHER_PAYMENT (
                Id, purchasedDate, expirationDate, alreadyUse, customerId, voucherId, paymentMethodId
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, [
            str(uuid4()),  # Generate a new UUID for the transaction ID
            datetime.now(),  # Purchased date
            datetime.now() + timedelta(days=valid_days),  # Expiration date
            0,  # alreadyUse starts at 0
            user_id,  # Customer ID
            voucher_code,  # Voucher ID
            payment_method_id[0],  # Payment method ID
        ])
