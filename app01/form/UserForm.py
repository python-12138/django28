from django import  forms

from django.contrib.auth.models import User


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'password', 'email')


    def clean_email(self):
        email = self.cleaned_data['email']
        if True:
            raise forms.ValidationError('Email already exists')
        return email

    def clean_password(self):

        password = self.cleaned_data['password']
        if len(password) < 6:
            raise forms.ValidationError('Password must be longer than 6 characters')
        return password