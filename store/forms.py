from django import forms
from .models import Category,Product, ProductImage, Offer
from django.forms.widgets import ClearableFileInput

class ProductForm(forms.ModelForm):
    sizes = forms.CharField(
        required=False,
        help_text="Enter sizes separated by commas (e.g., S, M, L, XL)."
    )

    class Meta:
        model = Product
        fields = ['product_name', 'category', 'description', 'specification', 'product_price', 'sale_price', 'quantity', 'main_image', 'sizes']

    def save(self, commit=True):
        product = super().save(commit=False)
        if self.cleaned_data['sizes']:
            product.sizes = [size.strip() for size in self.cleaned_data['sizes'].split(',')]
        if commit:
            product.save()
        return product

class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['image']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description', 'is_listed']

class MultiFileInput(ClearableFileInput):
    def __init__(self, attrs=None):
        super().__init__(attrs)
        if attrs is None:
            attrs = {}
        attrs.update({'multiple': True})
        self.attrs = attrs

class CouponForm(forms.Form):
    coupon_code = forms.CharField(max_length=50, required=False)
