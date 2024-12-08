from django.shortcuts import render
from django.db import connection  

def discount_page(request):
    with connection.cursor() as cursor:
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

    context = {
        'vouchers': vouchers,
        'promos': promos,
    }
    return render(request, 'discount.html', context)

from django.shortcuts import render, redirect
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import JsonResponse
from django.db import connection
from datetime import datetime, timedelta

def buy_voucher(request):
    if request.method == 'POST':
        voucher_code = request.POST.get('voucher_code', None)
        if not voucher_code:
            return JsonResponse({
                'success': False,
                'message': 'Voucher code is missing.',
            })

        
        with connection.cursor() as cursor:
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

        
        user_id = request.session.get('user_id')
        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'User not authenticated. Please login first.',
            })

        # Ambil MyPayBalance user
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT MyPayBalance
                FROM sijarta.APP_USER
                WHERE Id = %s
            """, [str(user_id)])
            row = cursor.fetchone()

        if row:
            user_balance = float(row[0]) 
        else:
            return JsonResponse({
                'success': False,
                'message': 'User not found in the database.',
            })


        if user_balance >= float(price):
            new_balance = user_balance - float(price)
            with connection.cursor() as cursor:
                cursor.execute("""
                    UPDATE sijarta.APP_USER
                    SET MyPayBalance = %s
                    WHERE Id = %s
                """, [new_balance, str(user_id)])


            valid_until = (datetime.now() + timedelta(days=valid_days)).strftime('%d/%m/%Y')

            return JsonResponse({
                'success': True,
                'message': f'Voucher {voucher_code} purchased successfully!',
                'valid_until': valid_until,
                'usage_quota': user_quota,
                'remaining_balance': new_balance,
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Sorry, your balance is not enough to buy this voucher.',
            })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.',
    })
