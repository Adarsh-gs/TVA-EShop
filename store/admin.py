from django.contrib import admin
from .models import UserProfile, Product, ProductImage, Category
from django import forms
from .models import Payment_model

admin.site.register(Payment_model)

class ProductAdminForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'category', 'description', 'product_price', 'sale_price', 'quantity']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('sno', 'user', 'email', 'is_active')
    search_fields = ('user', 'email', 'user__username')
    list_filter = ('is_active',)

    def email(self, obj):
        return obj.user.email

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm  
    list_display = ('product_name', 'category', 'product_price', 'quantity', 'sizes')
    search_fields = ('product_name', 'category')
    list_filter = ('category',)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_filter = ('is_listed', 'is_deleted')


