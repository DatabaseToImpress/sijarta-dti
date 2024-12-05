from django import forms


class LoginForm(forms.Form):
    phone_number = forms.CharField(max_length=15, label="Phone Number")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")


class RegisterUserForm(forms.Form):
    name = forms.CharField(max_length=100, label="Name")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    sex = forms.ChoiceField(choices=[('F', 'Female'), ('M', 'Male')], label="Sex")
    phone_number = forms.CharField(max_length=15, label="Phone Number")
    birth_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), label="Birth Date")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Address")

class RegisterWorkerForm(forms.Form):
    name = forms.CharField(max_length=100, label="Name")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")
    sex = forms.ChoiceField(choices=[('F', 'Female'), ('M', 'Male')], label="Sex")
    phone_number = forms.CharField(max_length=15, label="Phone Number")
    birth_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), label="Birth Date")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Address")
    bank_name = forms.ChoiceField(
        choices=[
            ('GoPay', 'GoPay'),
            ('OVO', 'OVO'),
            ('BCA', 'Virtual Account BCA'),
            ('BNI', 'Virtual Account BNI'),
            ('Mandiri', 'Virtual Account Mandiri')
        ],
        label="Bank Name"
    )
    account_number = forms.CharField(max_length=20, label="Account Number")
    npwp = forms.CharField(max_length=20, label="NPWP")
    image_url = forms.URLField(label="Image URL")


class UpdateProfileUserForm(forms.Form):
    name = forms.CharField(max_length=100, label="Name")
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep current password'}),
        required=False,
        label="Password"
    )
    sex = forms.ChoiceField(choices=[('F', 'Female'), ('M', 'Male')], label="Sex")
    phone_number = forms.CharField(max_length=15, label="Phone Number")
    birth_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), label="Birth Date")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Address")


class UpdateProfileWorkerForm(forms.Form):
    name = forms.CharField(max_length=100, label="Name")
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep current password'}),
        required=False,
        label="Password"
    )
    sex = forms.ChoiceField(choices=[('F', 'Female'), ('M', 'Male')], label="Sex")
    phone_number = forms.CharField(max_length=15, label="Phone Number")
    birth_date = forms.DateField(widget=forms.TextInput(attrs={'type': 'date'}), label="Birth Date")
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Address")
    bank_name = forms.CharField(max_length=100, label="Bank Name", required=False)
    account_number = forms.CharField(max_length=20, label="Account Number", required=False)
    npwp = forms.CharField(max_length=20, label="NPWP", required=False)
