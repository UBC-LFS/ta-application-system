from django import forms


class LocalLoginForm(forms.Form):
    username = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={ 'placeholder': 'Enter your username' })
    )
    password = forms.CharField(
        max_length=200,
        widget=forms.PasswordInput(attrs={ 'placeholder': 'Enter your password' })
    )
