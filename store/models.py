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

    def apply_discount(self, total_amount):
        if self.discount_type == 'percent':
            return total_amount * (1 - self.discount_value / 100)
        elif self.discount_type == 'flat':
            return total_amount - self.discount_value
        return total_amount

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

class Offer(models.Model):
    offer_code = models.CharField(max_length=100)
    offer_type = models.CharField(max_length=100)
    discount_type = models.CharField(max_length=50, default='') 
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    starting_date = models.DateField(default='2025-01-01')
    expiration_date = models.DateField()
    is_referral_offer = models.BooleanField(default=False) 

    def __str__(self):
        return self.offer_code

class Referral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral", verbose_name="Referrer")
    code = models.CharField(max_length=10, unique=True, verbose_name="Referral Code")
    referred_users = models.ManyToManyField(User, related_name="referred_by", blank=True)

    def __str__(self):
        return f"{self.user.username}'s referral code: {self.code}"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

