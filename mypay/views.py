from django.shortcuts import render


def mypay_transaction_form_view(request):
    return render(request, 'mypay_transaction.html')

# Create your views here.
def mypay_view(request):
    return render(request, 'mypay.html')  # No context needed for placeholders

def servicejob_view(request):
    return render(request, 'servicejob.html')  # No context needed for placeholders

def servicejob_status_view(request):
    return render(request, 'servicejob_status.html')