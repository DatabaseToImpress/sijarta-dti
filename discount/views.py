from django.shortcuts import render


def discount_page(request):
    return render(request, 'discount.html')


