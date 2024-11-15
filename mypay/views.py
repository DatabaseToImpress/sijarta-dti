from django.shortcuts import render
from .forms import MyPayTransactionForm

def mypay_transaction_form_view(request):
    form = MyPayTransactionForm()  # Instantiate the form
    return render(request, 'mypay_transaction.html', {'form': form})

# Create your views here.
def mypay_view(request):
    return render(request, 'mypay.html')  # No context needed for placeholders
