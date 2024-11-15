from django import forms

class MyPayTransactionForm(forms.Form):
    TRANSACTION_TYPES = [
        ('topup', 'Top Up'),
        ('payment', 'Service Payment'),
        ('transfer', 'Transfer'),
        ('withdrawal', 'Withdrawal'),
    ]

    transaction_category = forms.ChoiceField(
        choices=TRANSACTION_TYPES, 
        required=True, 
        label="Transaction Category",
        widget=forms.Select(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )

    topup_amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False, 
        label="Top-Up Amount",
        widget=forms.NumberInput(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )

    service_session = forms.CharField(
        max_length=100, 
        required=False, 
        label="Service Session",
        widget=forms.TextInput(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )

    service_price = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False, 
        label="Service Price", 
        initial=0.00,
        widget=forms.NumberInput(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )

    recipient_phone = forms.CharField(
        max_length=15, 
        required=False, 
        label="Recipient's Phone Number",
        widget=forms.TextInput(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )

    transfer_amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False, 
        label="Transfer Amount",
        widget=forms.NumberInput(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )

    bank_name = forms.CharField(
        max_length=100, 
        required=False, 
        label="Bank Name",
        widget=forms.TextInput(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )

    bank_account_number = forms.CharField(
        max_length=50, 
        required=False, 
        label="Bank Account Number",
        widget=forms.TextInput(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )

    withdrawal_amount = forms.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        required=False, 
        label="Withdrawal Amount",
        widget=forms.NumberInput(attrs={'class': 'w-full bg-gray-700 text-white p-2 rounded'})
    )
