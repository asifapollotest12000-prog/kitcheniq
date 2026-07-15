from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, InventoryItem

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address'}),
        }

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['designation', 'profile_pic_url', 'currency']
        widgets = {
            'designation': forms.TextInput(attrs={'placeholder': 'e.g., Operations Manager'}),
            'profile_pic_url': forms.TextInput(attrs={'placeholder': 'e.g., https://unsplash.com/... (Image URL)'}),
            'currency': forms.Select(),
        }

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'purchase_item_name', 'generic_item_name', 'category', 
            'storage_location', 'kitchen_location', 'purchase_unit', 
            'recipe_unit', 'par_level', 'qty_on_hand', 'unit_price', 'recipe_unit_price',
            'audit', 'audit_notes'
        ]
        labels = {
            'unit_price': 'Purchase Unit Price',
            'recipe_unit_price': 'Recipe Unit Price',
        }
        widgets = {
            'purchase_item_name': forms.TextInput(attrs={'placeholder': 'e.g., Whole Chicken'}),
            'generic_item_name': forms.TextInput(attrs={'placeholder': 'e.g., Chicken', 'list': 'genericNamesDatalist'}),
            'category': forms.Select(),
            'storage_location': forms.Select(),
            'kitchen_location': forms.Select(),
            'purchase_unit': forms.Select(),
            'recipe_unit': forms.Select(),
            'par_level': forms.NumberInput(attrs={'placeholder': 'e.g., 10.0', 'step': '0.01'}),
            'qty_on_hand': forms.NumberInput(attrs={'value': '0.00', 'readonly': 'readonly', 'step': '0.01', 'min': '0', 'max': '999'}),
            'unit_price': forms.NumberInput(attrs={'placeholder': 'e.g., 4.50', 'step': '0.01'}),
            'recipe_unit_price': forms.NumberInput(attrs={'placeholder': 'e.g., 0.15', 'step': '0.01'}),
            'audit': forms.Select(),
            'audit_notes': forms.TextInput(attrs={'placeholder': 'Audit notes...', 'maxlength': '50', 'list': 'auditNotesDatalist'}),
        }


