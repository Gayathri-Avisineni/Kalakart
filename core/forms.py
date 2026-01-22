from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
from .models import Review
from .models import SellerProfile
from .models import Product

class CustomUserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class':'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class':'form-control'}))
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={'class':'form-control'}))

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other','Other')
    ]
    gender = forms.ChoiceField(choices=GENDER_CHOICES, widget=forms.RadioSelect(attrs={'class':'form-check-input me-2'}), required=True)

    ACCOUNT_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
    ]
    account_type = forms.ChoiceField(choices=ACCOUNT_CHOICES, widget=forms.RadioSelect(attrs={'class':'form-check-input me-2'}), required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'phone', 'password1', 'password2', 'gender', 'account_type']



class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['profile_picture']




class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Write your review...'})
        }



class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = SellerProfile
        fields = ['full_name', 'store_name', 'location', 'bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3}),
        }




class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'price',
            'mrp',
            'material',
            'color',
            'quantity',
            'image',
            'category',
            'region',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter product name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter product description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter price'}),
            'mrp': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter MRP (optional)'}),
            'material': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Material type'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Color'}),
            'quantity': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Available quantity'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'region': forms.Select(attrs={'class': 'form-select'}),
        }
