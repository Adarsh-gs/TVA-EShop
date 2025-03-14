from django.db import models
from django.contrib.auth.models import User 
from django.db import models
from django.utils import timezone
from django.utils.timezone import now

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, unique=True)
    sno = models.AutoField(primary_key=True)
    usname = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} ({self.user.email})" if self.user else "User Profile"
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True, default='default.jpg')
    mobile = models.CharField(max_length=15, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user.username} - {self.otp}"

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_deleted = models.BooleanField(default=False)
    is_listed = models.BooleanField(default=True) 

    def __str__(self):
        return self.name

class Product(models.Model):
    product_name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    specification = models.TextField(default='No specification available')
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    sizes = models.CharField(max_length=255, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    main_image = models.ImageField(upload_to='main_product_images/', null=True, blank=True)
    colors = models.CharField(max_length=255, blank=True, null=True) 

    def __str__(self):
        return self.product_name

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='product_images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return f"Image for {self.product.product_name}"

class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    reviewer_name = models.CharField(max_length=100)
    email = models.EmailField()
    rating = models.IntegerField()
    review_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.reviewer_name} for {self.product.product_name}"

from django.db import models
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)  
    discount_type = models.CharField(choices=[('percent', 'Percentage'), ('flat', 'Flat Amount')], max_length=10)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2) 
    expiration_date = models.DateField(null=True, blank=True) 
    is_active = models.BooleanField(default=True) 

    def __str__(self):
        return self.code

    def is_expired(self):
        return self.expiration_date and self.expiration_date < timezone.now().date()

    def apply_discount(self, total_price):
        if self.discount_type == 'percent':
            discount = (self.discount_value / 100) * total_price
        else: 
            discount = self.discount_value
        
        return min(discount, total_price).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class CouponUsage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'coupon')  

    def __str__(self):
        return f"{self.user.username} used {self.coupon.code}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    selected_size = models.CharField(max_length=50, blank=True, null=True)
    selected_color = models.CharField(max_length=50, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def total_price(self):
        return self.quantity * self.product.sale_price

    def __str__(self):
        return f"{self.user.username} - {self.product.product_name} ({self.selected_size}, {self.selected_color})"

class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=50, default="Pending")
    payment_status = models.CharField(max_length=50, default="Pending")
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=50, default="cash_on_delivery")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    items = models.ManyToManyField(Product, through='OrderItem')
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"

class OrderItem(models.Model): 
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)
    selected_size = models.CharField(max_length=50, blank=True, null=True)
    selected_color = models.CharField(max_length=50, blank=True, null=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    status = models.CharField(max_length=50, default="Pending")

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity} in Order {self.order.id}"

class Payment_model(models.Model):
    name = models.CharField(max_length=100)
    amount = models.CharField(max_length=100)
    order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    paid = models.BooleanField(default=False)

    class Meta:
        db_table = 'store_payment_model'

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'product')  

from django.db import models
from django.utils import timezone

class Offer(models.Model):
    OFFER_TYPES = (
        ('product', 'Product Offer'),
        ('category', 'Category Offer'),
        ('referral', 'Referral Offer'),
    )
    DISCOUNT_TYPES = (
        ('percentage', 'Percentage'),
        ('amount', 'Fixed Amount'),
    )
    
    offer_type = models.CharField(max_length=100, choices=OFFER_TYPES)
    discount_type = models.CharField(max_length=50, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    starting_date = models.DateField(default='2025-01-01')
    expiration_date = models.DateField()
    is_referral_offer = models.BooleanField(default=False)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.get_offer_type_display()} - {self.discount_value}{'%' if self.discount_type == 'percentage' else '₹'}"
    
class Referral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral", verbose_name="Referrer")
    code = models.CharField(max_length=10, unique=True, verbose_name="Referral Code")
    referred_users = models.ManyToManyField(User, related_name="referred_by", blank=True)

    def __str__(self):
        return f"{self.user.username}'s referral code: {self.code}"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=6, choices=TRANSACTION_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.transaction_type} of ₹{self.amount} for {self.user.username} on {self.created_at}"

    class Meta:
        ordering = ['-created_at']