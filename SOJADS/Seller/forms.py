# Seller/forms.py
from django import forms
from .models import Product, ProductImage
from django import forms
from .models import Reply


class ProductForm(forms.ModelForm):
    
    class Meta:
        model = Product
        fields = ['product_name', 'price', 'category', 'description', 'discount']
        


RATING_CHOICES = [
    ('', 'All Ratings'),
    ('1', '1 Star'),
    ('2', '2 Stars'),
    ('3', '3 Stars'),
    ('4', '4 Stars'),
    ('5', '5 Stars'),
]

class ProductImageForm(forms.ModelForm):
    
    class Meta:
        model = ProductImage
        fields = ['image']
        

class ReviewFilterForm(forms.Form):
    search = forms.CharField(required=False)
    rating = forms.ChoiceField(
        choices=[('', 'All')] + [(i, i) for i in range(1, 6)],
        required=False
    )

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={
                'class': 'border rounded py-2 px-4 w-full',
                'placeholder': 'Write your reply...'
            })
        }