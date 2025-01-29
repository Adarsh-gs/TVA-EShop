from PIL import Image
import razorpay
import openpyxl
from reportlab.pdfgen import canvas
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import never_cache
from .forms import ProductForm, CategoryForm, CouponForm
from .models import Product, UserProfile, ProductImage, Category, Review, Referral, Coupon, Cart, Address, Order, OrderItem, Wishlist, Payment_model, UserOTP, Offer 
from .models import Offer, Wallet, Order
from django.core.paginator import Paginator
from django.core.mail import send_mail
from .utils import generate_otp
from django.http import JsonResponse, HttpResponse
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count
from django.utils.timezone import datetime
from django.shortcuts import render
from django.db import transaction
from urllib.parse import unquote
from . signals import generate_referral_code
from datetime import date
from django.shortcuts import render, get_object_or_404, redirect
from .forms import OfferForm
from django.shortcuts import get_object_or_404, redirect, render
from .forms import OfferForm 
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, F, Value
from django.db.models.functions import Coalesce
from .utils import generate_pdf, generate_excel
from decimal import Decimal
import json


#client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
client = razorpay.Client(auth=('rzp_test_HvfDTnynQgq7lg', '8neoukvKqUSfNB7Ik8DbZlfr'))



@login_required(login_url='login_view')
def home_page(request):
    products = Product.objects.filter(is_deleted=False)
    fashion_category = Category.objects.get(name='Fashion & Beauty')
    kids_category = Category.objects.get(name='Kids & Babies Clothes')
    men_category = Category.objects.get(name='Men Clothes')
    women_category = Category.objects.get(name='Women Clothes')

    sort_by = request.GET.get('sort_by', '')
    if sort_by == 'popularity':
        products = products.annotate(review_count=Count('reviews')).order_by('-review_count')
    elif sort_by == 'new_arrivals':
        products = products.order_by('-created_at')

    category_name = request.GET.get('category', '').strip()
    if category_name:
        category_name = unquote(category_name)  
        print(f"Filtering by category: {category_name}")
        try:
            category = Category.objects.get(name__iexact=category_name)
            products = products.filter(category=category)
        except Category.DoesNotExist:
            print(f"Category '{category_name}' not found.")
            products = products.none()

    return render(request, 'index.html', {
        'products': products,        
        'fashion_category': fashion_category,
        'kids_category': kids_category,
        'men_category': men_category,
        'women_category': women_category,
    })

@never_cache
def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        referral_code = request.POST['referral_code']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists. Please choose another one.')
                return redirect('signup')
            
            if User.objects.filter(email=email).exists():
                messages.error(request, 'Email is already registered. Please use another email.')
                return redirect('signup')

            referrer = None
            if referral_code:
                try:
                    referrer = Referral.objects.get(code=referral_code)
                except Referral.DoesNotExist:
                    messages.error(request, 'Referral code does not exist. Please use a valid one.')
                    return redirect('signup')

            user = User.objects.create_user(username=username, email=email, password=password1)
            user.save()

            if referrer:
                referrer.referred_users.add(user)
                referrer.save()

                referrer_wallet, created = Wallet.objects.get_or_create(user=referrer.user)
                referrer_wallet.balance += 100
                referrer_wallet.save()

                new_user_wallet = Wallet.objects.create(user=user, balance=50)
                new_user_wallet.save()
            else:
                Wallet.objects.create(user=user)

            if not Referral.objects.filter(user=user).exists():
                referral_code_generated = generate_referral_code() 
                Referral.objects.create(user=user, code=referral_code_generated)

            otp = generate_otp()
            UserOTP.objects.create(user=user, otp=otp)
            
            send_mail(
                'Your OTP for TVA E-Shop',
                f'Your OTP is {otp}. Please verify to complete registration.',
                'noreply@tvaeshop.com',
                [email],
                fail_silently=False,
            )
            
            messages.success(request, 'OTP sent to your email. Please verify.')
            return redirect('verify_otp')
        else:
            messages.error(request, 'Passwords do not match.')
    return render(request, 'signup.html')

# Login view
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('Home_page')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user_instance = User.objects.get(email=email)
            if not user_instance.is_active:
                messages.error(request, "Your account has been blocked by the admin.")
                return render(request, 'login.html')

            user = authenticate(request, username=user_instance.username, password=password)
            if user:
                login(request, user)
                return redirect('Home_page')
            else:
                messages.error(request, "Invalid credentials!")
        except User.DoesNotExist:
            messages.error(request, "User does not exist!")

    return render(request, 'login.html')

# OTP Verification view
def verify_otp(request):
    if request.method == "POST":
        email_or_mobile = request.POST.get('email_or_mobile')
        otp = request.POST.get('otp')

        user = User.objects.filter(email=email_or_mobile).first()
        if not user:
            messages.error(request, 'Email not registered.')
            return render(request, 'verify_otp.html')

        user_otp = UserOTP.objects.filter(user=user).first()
        if not user_otp:
            messages.error(request, 'No OTP request found for this user.')
            return render(request, 'verify_otp.html')

        if otp and user_otp.otp == otp:
            user.is_active = True
            user.save()
            user_otp.delete()
            messages.success(request, 'Account verified successfully.')
            return redirect('login_view')

        messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'verify_otp.html')

# Resend OTP view
def resend_otp(request):
    if request.method == 'POST':
        email_or_mobile = request.POST.get('email_or_mobile')

        user = User.objects.filter(email=email_or_mobile).first()
        if not user:
            return JsonResponse({'success': False, 'message': 'User not found.'})

        otp = generate_otp()
        user_otp, created = UserOTP.objects.update_or_create(user=user, defaults={'otp': otp})

        send_mail(
            'Your OTP for TVA E-Shop',
            f'Your OTP is {otp}. Please verify to complete registration.',
            'noreply@tvaeshop.com',
            [user.email],
            fail_silently=False,
        )

        return JsonResponse({'success': True, 'message': 'OTP resent successfully.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})

# Password reset view
def forget_pass(request):
    if request.method == 'POST':
        contact = request.POST.get('contact')
        otp = request.POST.get('otp')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if otp:
            try:
                user_otp = UserOTP.objects.get(otp=otp, user__email=contact)
                if new_password == confirm_password:
                    user = user_otp.user
                    user.set_password(new_password)
                    user.save()
                    user_otp.delete() 
                    messages.success(request, 'Password reset successfully!')
                    return redirect('login_view')
                else:
                    messages.error(request, 'Passwords do not match. Please try again.')
            except UserOTP.DoesNotExist:
                messages.error(request, 'Invalid OTP. Please try again.')

        else:
            user = User.objects.filter(email=contact).first()
            if user:
                otp = generate_otp()
                user_otp = UserOTP.objects.create(user=user, otp=otp)

                send_mail(
                    'Your OTP for Password Reset',
                    f'Your OTP is {otp}. Please use it to reset your password.',
                    'noreply@tvaeshop.com',
                    [contact],
                    fail_silently=False,
                )

                messages.success(request, 'OTP sent to your email. Please verify.')
                return redirect('forget_pass')
            else:
                messages.error(request, 'No account found with this email.')

    return render(request, 'forget.html')

# Send OTP for password reset
def send_otp(request):
    if request.method == 'POST':
        contact = request.POST.get('contact')
        if contact:
            user = User.objects.filter(email=contact).first()
            if user:
                otp = generate_otp()
                user_otp = UserOTP.objects.create(user=user, otp=otp)
                send_mail(
                    'Your OTP for Password Reset',
                    f'Your OTP is {otp}. Please use it to reset your password.',
                    'noreply@tvaeshop.com',
                    [contact], 
                    fail_silently=False,
                )

                return JsonResponse({'success': True, 'message': 'OTP sent to your email. Please verify.'})

            else:
                return JsonResponse({'success': False, 'message': 'No account found with this email.'})
        else:
            return JsonResponse({'success': False, 'message': 'Please enter a valid contact.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

# Logout view
@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('login_view')

# Product list view
@login_required
def product_list(request):
    query = request.GET.get('q', '').strip()
    sort_by = request.GET.get('sort_by', '')
    filter_by = request.GET.get('filter', '')
    category_id = request.GET.get('category', None)
    men_category = Category.objects.get(name='Men Clothes')
    women_category = Category.objects.get(name='Women Clothes')
    fashion_category = Category.objects.get(name='Fashion & Beauty')
    kids_category = Category.objects.get(name='Kids & Babies Clothes')

    # Initialize products queryset
    products = Product.objects.filter(is_deleted=False)

    # Check if category_id is provided and filter by category
    if category_id:
        products = products.filter(category_id=category_id)

    # Apply search query filter
    if query:
        products = products.filter(product_name__icontains=query)

    # Sorting and filtering logic
    if sort_by == 'popularity':
        products = products.annotate(review_count=Count('reviews')).order_by('-review_count')
    elif sort_by == 'average_ratings':
        products = products.annotate(average_rating=Avg('reviews__rating')).order_by('average_rating')
    elif sort_by == 'new_arrivals':
        products = products.order_by('created_at')
    elif sort_by == 'az':
        products = products.order_by('product_name')
    elif sort_by == 'za':
        products = products.order_by('-product_name')

    if filter_by == 'price_low_to_high':
        products = products.order_by('sale_price')
    elif filter_by == 'price_high_to_low':
        products = products.order_by('-sale_price')

    # Pagination
    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Add ratings to products
    for product in page_obj:
        reviews = product.reviews.all()
        if reviews.exists():
            average_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        else:
            average_rating = 0

        full_stars = int(average_rating)
        half_star = 1 if (average_rating - full_stars) >= 0.5 else 0
        empty_stars = 5 - full_stars - half_star

        product.full_star_list = [1] * full_stars
        product.half_star_list = [1] * half_star
        product.empty_star_list = [1] * empty_stars

    return render(request, 'product-list.html', {
        'products': page_obj,
        'fashion_category': fashion_category,
        'kids_category': kids_category,
        'men_category': men_category,
        'women_category': women_category,
    })

# Product details view
@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    productss = Product.objects.filter(is_deleted=False)
    related_products = productss.exclude(id=product.id)[:4]
    
    reviews = product.reviews.all()

    # Check if the user has purchased the product
    has_purchased = OrderItem.objects.filter(order__user=request.user, product=product).exists()

    if reviews.exists():
        average_rating = sum([review.rating for review in reviews]) / reviews.count()
    else:
        average_rating = 0  

    full_stars = int(average_rating)
    half_star = 1 if (average_rating - full_stars) >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star

    full_star_list = [1] * full_stars
    half_star_list = [1] * half_star
    empty_star_list = [1] * empty_stars

    colors = product.colors.split(',') if product.colors else []

    try:
        sizes = json.loads(product.sizes) if product.sizes else []
    except json.JSONDecodeError:
        sizes = []

    for related_product in related_products:
        related_reviews = related_product.reviews.all()
        if related_reviews.exists():
            related_average_rating = sum([review.rating for review in related_reviews]) / related_reviews.count()
        else:
            related_average_rating = 0

        related_full_stars = int(related_average_rating)
        related_half_star = 1 if (related_average_rating - related_full_stars) >= 0.5 else 0
        related_empty_stars = 5 - related_full_stars - related_half_star

        related_product.full_star_list = [1] * related_full_stars
        related_product.half_star_list = [1] * related_half_star
        related_product.empty_star_list = [1] * related_empty_stars

    quantity = int(request.POST.get("quantity", 1)) 

    if request.method == "POST" and "reviewer_name" in request.POST:
        reviewer_name = request.POST.get("reviewer_name")
        email = request.POST.get("email")
        rating = request.POST.get("rating")
        review_text = request.POST.get("review_text")

        try:
            rating = int(rating)
        except ValueError:
            rating = 0 

        Review.objects.create(
            product=product,
            reviewer_name=reviewer_name,
            email=email,
            rating=rating,
            review_text=review_text,
        )
        return redirect("product_detail", product_id=product.id)

    return render(request, 'product-detail.html', {
        'product': product,
        'products': related_products, 
        'reviews': reviews, 
        'average_rating': average_rating,
        'full_star_list': full_star_list,
        'half_star_list': half_star_list,
        'empty_star_list': empty_star_list,
        'quantity': quantity, 
        'colors': colors, 
        'sizes': sizes,
        'has_purchased': has_purchased,  # Add this to the context
    })

# Cart view
@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items to proceed.")
        return render(request, 'cart.html', {
            'cart_items': cart_items,
            'total_price': 0,
            'discount': 0,
            'shipping_cost': 0,
            'grand_total': 0,
            'coupon': None,
        })

    total_price = sum(item.total_price() for item in cart_items)
    
    coupon = None
    discount = 0

    if request.method == "POST":
        if 'coupon_code' in request.POST:  # Apply coupon
            coupon_code = request.POST.get('coupon_code')
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                if coupon.is_expired():
                    messages.error(request, "The coupon has expired.")
                else:
                    discount = coupon.apply_discount(total_price)
                    messages.success(request, f"Coupon applied! You saved {coupon.discount_value}.")
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")
        
        elif 'remove_coupon' in request.POST:  # Remove coupon
            coupon = None
            discount = 0
            messages.success(request, "Coupon removed successfully.")

    shipping_cost = 1
    grand_total = total_price - discount + shipping_cost

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount': discount,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
        'coupon': coupon,
    })

# Add to cart view
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = request.POST.get('quantity', 1)
    selected_color = request.POST.get('selected_color') 
    selected_size = request.POST.get('selected_size')  

    try:
        quantity = int(quantity)
    except ValueError:
        quantity = 1

    if not selected_color or not selected_size:
        messages.error(request, "Please select a color and size.")
        return redirect('product_detail', product_id=product.id)

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('product_detail', product_id=product.id)

    if product.quantity == 0:
        messages.error(request, f"{product.product_name} is out of stock.")
        return redirect('product_detail', product_id=product.id)

    MAX_QTY_PER_PERSON = 5
    if quantity > MAX_QTY_PER_PERSON:
        messages.error(request, f"You can only add up to {MAX_QTY_PER_PERSON} of {product.product_name}.")
        return redirect('product_detail', product_id=product.id)

    if product.quantity < quantity:
        messages.error(request, f"Only {product.quantity} of {product.product_name} are available.")
        return redirect('product_detail', product_id=product.id)

    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)

    if not created:
        if cart_item.quantity + quantity > product.quantity:
            messages.error(
                request,
                f"Adding {quantity} would exceed available stock. "
                f"You already have {cart_item.quantity} in your cart."
            )
            return redirect('product_detail', product_id=product.id)

        if cart_item.quantity + quantity > MAX_QTY_PER_PERSON:
            messages.error(
                request,
                f"You cannot exceed the maximum limit of {MAX_QTY_PER_PERSON} for {product.product_name}."
            )
            return redirect('product_detail', product_id=product.id)

        cart_item.quantity += quantity
        cart_item.selected_color = selected_color
        cart_item.selected_size = selected_size
        cart_item.save()
        messages.success(request, f"{quantity} more of {product.product_name} added to your cart.")
    else:
        cart_item.selected_color = selected_color
        cart_item.selected_size = selected_size
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"{quantity} of {product.product_name} added to your cart.")

    return redirect('cart')

# Update the cart view
@login_required
@csrf_exempt
def update_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        cart_item.save()  
    return redirect('cart')

# Remove from cart view
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from your cart.")
    return redirect('cart')

# Add new Address
@login_required
def add_address(request):
    if request.method == 'POST':
        street = request.POST.get('address', '').strip()
        country = request.POST.get('country', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        zip_code = request.POST.get('zip', '').strip()

        if street and country and city and state and zip_code:
            Address.objects.create(
                user=request.user,
                street=street,
                city=city,
                state=state,
                zip_code=zip_code,
                country=country,
            )
            messages.success(request, "New address added successfully.")
            return redirect('Checkout')  
        else:
            messages.error(request, "Please provide all required address details.")
            return redirect('add_address') 
    return render(request, 'add_address.html')

# Edit the Address
@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        address.street = request.POST.get('address', '').strip()  
        address.city = request.POST.get('city', '').strip()
        address.state = request.POST.get('state', '').strip()
        address.zip_code = request.POST.get('zip', '').strip()
        address.country = request.POST.get('country', '').strip()
        address.save()
    

        messages.success(request, "Address updated successfully!")
        return redirect('Checkout')

    return render(request, 'edit_address.html', {'address': address})

# Wishlist view
@login_required
def wishlist(request):
    return render(request, 'wishlist.html')

# Add to wishlist
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        return JsonResponse({ 'message': 'Product is already in your wishlist!'})
    return JsonResponse({ 'message': 'Product added to wishlist!'})

# Remove from wishlist
@login_required
def remove_from_wishlist(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        Wishlist.objects.filter(user=request.user, product=product).delete()
        return JsonResponse({'message': 'Product removed from wishlist!'})
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=400)

@login_required
def my_account(request):
    user = request.user
    orders = Order.objects.filter(user=request.user).prefetch_related('orderitem_set__product')
    addresses = Address.objects.filter(user=user)
    referral = Referral.objects.filter(user=request.user).first()
    referred_users = referral.referred_users.all() if referral else []

    for order in orders:
        total_order_price = sum(item.price_at_time for item in order.orderitem_set.all())
        order.total_price = total_order_price

    try:
        wallet = Wallet.objects.get(user=user) 
    except Wallet.DoesNotExist:
        wallet = None

    if request.method == "POST" and "share_referral" in request.POST:
        if referral:
            referral_link = f"{request.build_absolute_uri('/signup/')}?ref={referral.code}"
            return render(request, "my_account.html", {
                "referral_link": referral_link,
                "referred_users": referred_users,
                "wallet_balance": wallet.balance if wallet else 0,
            })
        else:
            messages.error(request, "Referral code is not available.")
            return redirect("my_account")

    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user.first_name = request.POST['first_name']
            user.last_name = request.POST['last_name']
            user.email = request.POST['email']
            user.save()
            messages.success(request, 'Profile updated successfully!')

        elif 'change_password' in request.POST:
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password != confirm_password:
                messages.error(request, "New password and confirm password do not match.")
            else:
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password changed successfully!")
                return redirect('login_view')

        elif 'add_address' in request.POST:
            street = request.POST.get('address')
            city = request.POST.get('city')
            state = request.POST.get('state')
            zip_code = request.POST.get('zip')
            country = request.POST.get('country')

            if not street or not city or not state or not zip_code or not country:
                messages.error(request, "All address fields are required.")
            else:
                Address.objects.create(
                    user=user,
                    street=street,
                    city=city,
                    state=state,
                    zip_code=zip_code,
                    country=country,
                )
                messages.success(request, "New address added successfully!")

        elif 'edit_address' in request.POST:
            address_id = request.POST.get('edit_address')
            address = Address.objects.get(id=address_id, user=user)
            street = request.POST.get('address', address.street)
            city = request.POST.get('city', address.city)
            state = request.POST.get('state', address.state)
            zip_code = request.POST.get('zip', address.zip_code)
            country = request.POST.get('country', address.country)

            if not street or not city or not state or not zip_code or not country:
                messages.error(request, "All address fields are required.")
            else:
                address.street = street
                address.city = city
                address.state = state
                address.zip_code = zip_code
                address.country = country
                address.save()
                messages.success(request, "Address updated successfully!")

        elif 'delete_address' in request.POST:
            address_id = request.POST.get('delete_address')
            try:
                address = Address.objects.get(id=address_id, user=user)
                address.delete()
                messages.success(request, "Address deleted successfully!")
            except Address.DoesNotExist:
                messages.error(request, "Address not found.")

        elif 'cancel_order' in request.POST:
            order_id = request.POST.get('order_id')
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                if order.status != 'Cancelled':
                    order.status = 'Cancelled'
                    order.payment_status = 'Cancelled'
                    order.save()
                    messages.success(request, 'Order cancelled successfully!')
            except Order.DoesNotExist:
                messages.error(request, "Order not found.")

        elif 'return_order' in request.POST:
            order_id = request.POST.get('order_id')
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                if order.status == 'Delivered':
                    order.status = 'Returned'
                    order.save()
                    messages.success(request, 'Order returned successfully!')
                else:
                    messages.error(request, 'Order cannot be returned as it is not delivered.')
            except Order.DoesNotExist:
                messages.error(request, "Order not found.")

    return render(request, 'my-account.html', {
        'orders': orders,
        'addresses': addresses,
        "referral_code": referral.code if referral else None,
        "referred_users": referred_users,
        "wallet_balance": wallet.balance if wallet else 0,
    })

# Contact view
@login_required
def contact(request):
    return render(request, 'contact.html')

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# Checkout view
from django.db import transaction
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import razorpay
from .models import Order, Payment_model, Cart, Address, OrderItem
from django.conf import settings

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Add items before checking out.")
        return redirect('cart')

    total_price = sum(item.total_price() for item in cart_items)
    shipping_cost = 1
    grand_total = total_price + shipping_cost
    grand_total_in_paise = int(round(grand_total * 100))
    existing_addresses = Address.objects.filter(user=request.user)
    discount = 0
    razorpay_order_id = generate_razorpay_order_id(grand_total_in_paise)

    if request.method == "POST":
        payment_method = request.POST.get('payment_method', '').strip()

        if payment_method == "cod":
            return handle_cod_order(request, cart_items, grand_total, shipping_cost)

        elif payment_method == "razorpay":
            return initiate_razorpay_payment(request, cart_items, grand_total, grand_total_in_paise, shipping_cost)

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'discount': discount,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
        'grand_total_in_paise': grand_total_in_paise,
        'existing_addresses': existing_addresses,
        'razorpay_order_id': razorpay_order_id,
    })


def handle_cod_order(request, cart_items, grand_total, shipping_cost):
    try:
        with transaction.atomic():
            order = create_order(request, cart_items, grand_total, shipping_cost, "cod", "Pending")
            order.save()
            cart_items.delete()
        messages.success(request, "Order placed successfully via Cash on Delivery!")
        return redirect('order_complete', payment_method="cod")

    except Exception as e:
        messages.error(request, f"Order failed: {e}")
        return redirect('Checkout')


def initiate_razorpay_payment(request, cart_items, grand_total, grand_total_in_paise, shipping_cost):
    try:
        payment_order = client.order.create({
            'amount': grand_total_in_paise,
            'currency': 'INR',
            'payment_capture': '1',
        })
        razorpay_order_id = payment_order['id']

        with transaction.atomic():
            order = create_order(request, cart_items, grand_total, shipping_cost, "razorpay", "Pending", razorpay_order_id)
            order.save()
            cart_items.delete()
        return redirect('order_complete', payment_method="razorpay", razorpay_order_id=razorpay_order_id)

    except Exception as e:
        messages.error(request, f"Payment initialization failed: {e}")
        return redirect('Checkout')



@csrf_exempt
def order_complete(request, payment_method):
    if request.method == "POST":
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_order_id = request.POST.get('razorpay_order_id')
        payment_status = request.POST.get('status', 'failed')

        # Debugging statements
        print(f"🔹 Received Razorpay Order ID: {razorpay_order_id} (Type: {type(razorpay_order_id)})")
        print(f"🔹 Received Payment ID: {razorpay_payment_id}")

        if not razorpay_order_id:
            messages.error(request, "Payment processing error: Missing Razorpay Order ID.")
            return redirect('Checkout')

        # Ensure we are checking the correct type in the database
        try:
            order = Order.objects.filter(razorpay_order_id=str(razorpay_order_id)).first()
            if order:
                print(f"✅ Order Found: {order.id}, Razorpay Order ID: {order.razorpay_order_id} (Type: {type(order.razorpay_order_id)})")
            else:
                print(f"❌ No matching order found for ID: {razorpay_order_id}")
                print(f"🔎 Stored Order IDs: {list(Order.objects.values_list('razorpay_order_id', flat=True))}")
                messages.error(request, "Payment processing error: Order not found. Check if order ID was saved.")
                return redirect('Checkout')
        except Exception as e:
            print(f"🚨 Error while fetching order: {e}")
            messages.error(request, f"Database error: {e}")
            return redirect('Checkout')

        # Process the payment
        if payment_status == "success":
            try:
                with transaction.atomic():
                    order.payment_status = "Completed"
                    order.status = "Confirmed"
                    order.save()

                    Payment_model.objects.create(
                        name=order.user.username,
                        amount=str(order.total_price),
                        order_id=razorpay_order_id,
                        razorpay_payment_id=razorpay_payment_id,
                        paid=True
                    )
                
                messages.success(request, "Payment successful! Your order is confirmed.")
                return redirect('order_success')

            except Exception as e:
                messages.error(request, f"Payment processing error: {e}")
                return redirect('Checkout')

        else:
            messages.error(request, "Payment failed. Please try again.")
            return redirect('Checkout')

    return render(request, "order_complete.html", {"status": True})

def create_order(request, cart_items, grand_total, shipping_cost, payment_method, payment_status, razorpay_order_id=None):
    order = Order.objects.create(
        user=request.user,
        total_price=grand_total,
        shipping_cost=shipping_cost,
        payment_method=payment_method,
        payment_status=payment_status,
        status="Pending",
        razorpay_order_id=str(razorpay_order_id),
    )
    order.save()
    print(f"✅ Order Created: {order.id}, Razorpay Order ID: {order.razorpay_order_id}")

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price_at_time=item.product.sale_price,
            selected_size=item.selected_size,
            selected_color=item.selected_color,
            discount=0,
        )
        item.product.quantity -= item.quantity
        item.product.save()

    return order



def generate_razorpay_order_id(grand_total_in_paise):
    data = {
        "amount": grand_total_in_paise,
        "currency": "INR",
        "payment_capture": '1'
    }
    order = client.order.create(data=data)
    return order["id"]












def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "You must be logged in to access this page!")
            return redirect('login_view')
        if not request.user.is_superuser:
            messages.error(request, "You must be an admin to access this page!")
            return redirect('login_view')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Admin login view
def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user and user.is_superuser: 
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, "Invalid admin credentials!")
    
    return render(request, 'Admin/admin_login.html')

# Admin dashboard view
@admin_required
def admin_dashboard(request):
    return render(request, 'Admin/admin_dashboard.html')

# Admin users view
@admin_required
def admin_users(request):
    users = UserProfile.objects.select_related('user').exclude(user__is_superuser=True)

    filter_status = request.GET.get('filter', '')
    if filter_status == 'active':
        users = users.filter(is_active=True)
    elif filter_status == 'inactive':
        users = users.filter(is_active=False)

    sort_order = request.GET.get('sort', '')
    if sort_order == 'asc':
        users = users.order_by('name')
    elif sort_order == 'desc':
        users = users.order_by('-name')

    paginator = Paginator(users, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'Admin/admin_customers.html', {'customers': page_obj})

# Admin block user view
@admin_required
def block_user(request, user_id):
    user_profile = UserProfile.objects.get(sno=user_id)
    user_profile.is_active = False
    user_profile.save()

    user_profile.user.is_active = False
    user_profile.user.save()

    messages.success(request, f'User has been blocked successfully.')
    return redirect('admin_customers')

# Admin unblock user view
@admin_required
def unblock_user(request, user_id):
    user_profile = UserProfile.objects.get(sno=user_id)
    user_profile.is_active = True
    user_profile.save()

    user_profile.user.is_active = True
    user_profile.user.save()

    messages.success(request, f'User has been unblocked successfully.')
    return redirect('admin_customers')

# Admin category list view
@admin_required
def admin_category_list(request):
    categories = Category.objects.filter(is_deleted=False)
    return render(request, 'Admin/admin_category.html', {'categories': categories})

# Admin list view
@admin_required
def toggle_listed_status(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.is_listed = not category.is_listed 
    category.save()
    return redirect('admin_category')

# Admin add to category view
@admin_required
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_category')
        else:
            print(form.errors)
    else:
        form = CategoryForm()
    return render(request, 'Admin/admin_add_category.html', {'form': form})

# Admin update the category view
@admin_required
def edit_category(request, category_id):
    category = Category.objects.get(id=category_id)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            return redirect('admin_category')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'Admin/admin_edit_category.html', {'form': form})

# Admin soft delete category view
@admin_required
def soft_delete_category(request, category_id):
    category = Category.objects.get(id=category_id)
    category.is_deleted = True
    category.save()
    return redirect('admin_category')

# Admin products list view
@admin_required
def admin_products(request):
    products = Product.objects.filter(is_deleted=False).select_related('category').prefetch_related('product_images')
    return render(request, 'Admin/admin_product.html', {'products': products})

@admin_required
def admin_product_detail(request, product_id):
    product = Product.objects.get(pk=product_id, is_deleted=False)
    return render(request, 'Admin/admin_product_detail.html', {'product': product})

# Admin add to product view
@admin_required
def add_product(request):
    categories = Category.objects.filter(is_deleted=False)
    
    def resize_and_crop_image(image, target_width=800, target_height=800):
        try:
            img = Image.open(image)
            img = img.convert('RGB')
            img.thumbnail((target_width, target_height))
            
            left = (img.width - target_width) / 2
            top = (img.height - target_height) / 2
            right = (img.width + target_width) / 2
            bottom = (img.height + target_height) / 2
            img = img.crop((left, top, right, bottom))
            
            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)
            
            return InMemoryUploadedFile(img_io, None, image.name, 'image/jpeg', img_io.tell(), None)
        except Exception as e:
            messages.error(request, f"Error processing image: {str(e)}")
            return None

    def is_valid_image(file):
        valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
        file_extension = file.name.split('.')[-1].lower()
        return file_extension in valid_extensions

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new product instance
            product = form.save(commit=False)
            product.product_name = request.POST.get('product_name', product.product_name)
            category_id = request.POST.get('category')
            if category_id:
                product.category_id = int(category_id)
            else:
                messages.error(request, "Category is required.")
                return redirect(request.path_info)

            product.description = request.POST.get('description', product.description)
            product.specification = request.POST.get('specification', product.specification)
            product.product_price = request.POST.get('product_price', product.product_price)
            product.sale_price = request.POST.get('sale_price', product.sale_price)
            product.quantity = request.POST.get('quantity', product.quantity)

            # Handling sizes
            sizes = request.POST.get('sizes')
            if sizes:
                try:
                    sizes_list = [int(size.strip()) for size in sizes.split(',')]
                    product.sizes = json.dumps(sizes_list)
                except ValueError:
                    messages.error(request, "Invalid sizes input. Please enter numbers separated by commas.")
                    return redirect(request.path_info)

            # Handling colors
            colors = request.POST.get('colors')
            if colors:
                colors_list = [color.strip() for color in colors.split(',')]
                if not all(colors_list):
                    messages.error(request, "Invalid colors input. Colors cannot be empty.")
                    return redirect(request.path_info)
                product.colors = ','.join(colors_list)
            else:
                product.colors = ""
            form = ProductForm(request.POST, request.FILES)
            # Handle resizing and saving main image
            main_image = request.FILES.get('main_image')
            if not main_image:
                messages.error(request, "Main image is required.")
                return render(request, 'Admin/admin_product_add.html', {'form': form, 'categories': categories})
            
            if not is_valid_image(main_image):
                messages.error(request, "Invalid file type for the main image. Please upload an image file (JPG, JPEG, PNG, GIF).")
                return render(request, 'Admin/admin_product_add.html', {'form': form, 'categories': categories})
            
            processed_main_image = resize_and_crop_image(main_image)
            if processed_main_image:
                product.main_image = processed_main_image
            else:
                return render(request, 'Admin/admin_product_add.html', {'form': form, 'categories': categories})

            # Save the product instance
            product.save()

            # Handle product images
            product_images = request.FILES.getlist('product_images')
            if len(product_images) < 3:
                messages.error(request, "At least 3 product images are required.")
                return render(request, 'Admin/admin_product_add.html', {'form': form, 'categories': categories})
            
            for img in product_images:
                if is_valid_image(img):
                    processed_img = resize_and_crop_image(img)
                    if processed_img:
                        ProductImage.objects.create(product=product, image=processed_img)
                    else:
                        messages.error(request, f"Error processing the image: {img.name}")
                        return render(request, 'Admin/admin_product_add.html', {'form': form, 'categories': categories})
                else:
                    messages.error(request, f"Invalid file type for the product image: {img.name}")
                    return render(request, 'Admin/admin_product_add.html', {'form': form, 'categories': categories})
            
            messages.success(request, "Product added successfully!")
            return redirect('admin_products')
        else:
            messages.error(request, "Form validation failed. Please correct the highlighted errors.")
    else:
        form = ProductForm()

    return render(request, 'Admin/admin_product_add.html', {'form': form, 'categories': categories})

# Admin update the product view
@admin_required
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = get_list_or_404(Category)

    def resize_and_crop_image(image, target_width=800, target_height=800):
        try:
            img = Image.open(image)
            img = img.convert('RGB')
            img.thumbnail((target_width, target_height))
            left = (img.width - target_width) / 2
            top = (img.height - target_height) / 2
            right = (img.width + target_width) / 2
            bottom = (img.height + target_height) / 2
            img = img.crop((left, top, right, bottom))

            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            img_io.seek(0)

            return InMemoryUploadedFile(img_io, None, image.name, 'image/jpeg', img_io.tell(), None)
        except Exception as e:
            messages.error(request, f"Error processing image: {str(e)}")
            return None

    def is_valid_image(file):
        valid_extensions = ['jpg', 'jpeg', 'png', 'gif']
        file_extension = file.name.split('.')[-1].lower()
        return file_extension in valid_extensions

    if request.method == 'POST':
        product.product_name = request.POST.get('product_name', product.product_name)
        category_id = request.POST.get('category')
        if category_id:
            product.category_id = int(category_id)
        else:
            messages.error(request, "Category is required.")
            return redirect(request.path_info)

        product.description = request.POST.get('description', product.description)
        product.specification = request.POST.get('specification', product.specification)
        product.product_price = request.POST.get('product_price', product.product_price)
        product.sale_price = request.POST.get('sale_price', product.sale_price)
        product.quantity = request.POST.get('quantity', product.quantity)

        # Handling sizes
        sizes = request.POST.get('sizes')
        if sizes:
            try:
                sizes_list = [int(size.strip()) for size in sizes.split(',')]
                product.sizes = json.dumps(sizes_list)
            except ValueError:
                messages.error(request, "Invalid sizes input. Please enter numbers separated by commas.")
                return redirect(request.path_info)

        # Handling colors
        colors = request.POST.get('colors')
        if colors:
            colors_list = [color.strip() for color in colors.split(',')]
            if not all(colors_list):
                messages.error(request, "Invalid colors input. Colors cannot be empty.")
                return redirect(request.path_info)
            product.colors = ','.join(colors_list)
        else:
            product.colors = ""

        # Handling main image
        main_image = request.FILES.get('main_image')
        if main_image:
            if not is_valid_image(main_image):
                messages.error(request, "Invalid file type for the main image. Please upload an image file (JPG, JPEG, PNG, GIF).")
                return redirect(request.path_info)
            processed_main_image = resize_and_crop_image(main_image)
            if processed_main_image:
                product.main_image = processed_main_image
            else:
                return redirect(request.path_info)

        # Handling product images
        product_images = request.FILES.getlist('product_images')
        if product_images:
            for img in product_images:
                if not is_valid_image(img):
                    messages.error(request, f"Invalid file type for a product image: {img.name}. Please upload image files (JPG, JPEG, PNG, GIF).")
                    return redirect(request.path_info)
                processed_img = resize_and_crop_image(img)
                if processed_img:
                    ProductImage.objects.create(product=product, image=processed_img)
                else:
                    messages.error(request, f"Error processing an image: {img.name}")
                    return redirect(request.path_info)

        # Handling deletion of images
        delete_image_ids = request.POST.getlist('delete_images')
        if delete_image_ids:
            delete_image_ids = [int(id) for id in delete_image_ids]
            ProductImage.objects.filter(id__in=delete_image_ids).delete()

        product.save()
        messages.success(request, "Product updated successfully!")
        return redirect('admin_products')

    else:
        if product.sizes:
            try:
                sizes_list = json.loads(product.sizes)
                sizes_initial = ', '.join(map(str, sizes_list)) if isinstance(sizes_list, list) else str(sizes_list)
            except (json.JSONDecodeError, TypeError):
                sizes_initial = str(product.sizes)
        else:
            sizes_initial = ''

    existing_images = product.product_images.all()

    return render(request, 'Admin/admin_product_edit.html', {
        'product': product,
        'existing_images': existing_images,
        'sizes_initial': sizes_initial,
        'categories': categories,
    })

# Admin delete product view
@admin_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_deleted = True
    product.save()
    return redirect('admin_products')

# Admin orders list view
@admin_required
def orders_view(request):
    orders = Order.objects.all()

    if request.method == 'POST':
        if 'cancel_order' in request.POST:
            order_id = request.POST.get('order_id')
            try:
                order = Order.objects.get(id=order_id)
                order.status = 'Cancelled'  
                order.payment_status = 'Cancelled' 
                order.save() 
                messages.success(request, f"Order {order_id} has been cancelled and payment status updated.")
            except Order.DoesNotExist:
                messages.error(request, "Order not found.")
    
    context = {'orders': orders}
    return render(request, 'Admin/admin_orders.html', context)

@admin_required
def update_order_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            new_status = data.get('status')
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()

            return JsonResponse({'success': True, 'message': 'Order status updated.'})
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})

# Admin banner view
@admin_required
def admin_banner(request):
    return render(request, 'Admin/admin_banner.html')

# Admin sales list view
@admin_required
def admin_sales(request):
    return render(request, 'Admin/admin_sales_report.html')

def sales_report(request):
    period = request.GET.get('period')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if period == 'daily':
        orders = Order.objects.filter(order_date__date=datetime.date.today())
    elif period == 'weekly':
        week_ago = datetime.date.today() - datetime.timedelta(days=7)
        orders = Order.objects.filter(order_date__gte=week_ago)
    elif period == 'monthly':
        month_start = datetime.date.today().replace(day=1)
        orders = Order.objects.filter(order_date__gte=month_start)
    elif start_date and end_date:
        orders = Order.objects.filter(order_date__range=[start_date, end_date])
    else:
        orders = Order.objects.all()

    total_sales = orders.aggregate(total=Coalesce(Sum(F('price') * F('quantity')), 0))['total']
    total_discount = orders.aggregate(total=Coalesce(Sum('discount'), 0))['total']
    total_orders = orders.count()

    context = {
        'orders': orders,
        'total_sales': total_sales,
        'total_discount': total_discount,
        'total_orders': total_orders,
    }
    return render(request, 'sales_report.html', context)

def fetch_filtered_orders(query_params):
    period = query_params.get('period')
    start_date = query_params.get('start_date')
    end_date = query_params.get('end_date')

    if period == 'daily':
        orders = Order.objects.filter(order_date__date=datetime.date.today())
    elif period == 'weekly':
        week_ago = datetime.date.today() - datetime.timedelta(days=7)
        orders = Order.objects.filter(order_date__gte=week_ago)
    elif period == 'monthly':
        month_start = datetime.date.today().replace(day=1)
        orders = Order.objects.filter(order_date__gte=month_start)
    elif start_date and end_date:
        orders = Order.objects.filter(order_date__range=[start_date, end_date])
    else:
        orders = Order.objects.all()
    
    return orders

def download_report(request, file_type):
    orders = fetch_filtered_orders(request.GET) 
    if file_type == 'pdf':
        response = generate_pdf_report(orders)
    elif file_type == 'excel':
        response = generate_excel_report(orders)
    return response

def generate_pdf_report(data):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 750, "Sales Report")
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

def generate_excel_report(data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Report"
    ws.append(["Order ID", "Buyer", "Product(s)", "Total Price"])  

    for order in data:
        product_details = ", ".join([f"{item.product.product_name} x {item.quantity}" for item in order.orderitem_set.all()])
        ws.append([order.id, order.user.username, product_details, order.total_price])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        content=buffer.read(),
        content_type="application/vnd.ms-excel"
    )
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'
    return response

# Admin coupons list view
@admin_required
def admin_coupons(request):
    filter_type = request.GET.get('filter', 'all') 
    
    if filter_type == 'percentage':
        coupons = Coupon.objects.filter(discount_type='percent')
    elif filter_type == 'fixed':
        coupons = Coupon.objects.filter(discount_type='flat')
    else:
        coupons = Coupon.objects.all()
    
    return render(request, 'Admin/admin_coupons.html', {'coupons': coupons})

# Admin add to coupon view
@admin_required
def add_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        discount_type = request.POST.get('type') 
        discount_value = request.POST.get('amount') 
        expiration_date = request.POST.get('expiry_date') 

        Coupon.objects.create(
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            expiration_date=datetime.strptime(expiration_date, '%Y-%m-%d'),
            is_active=True 
        )
        
        return redirect('admin_coupons')

    return render(request, 'Admin/admin_add_coupon.html')

# Admin update the coupon view
@admin_required
def edit_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        coupon.code = request.POST.get('code')
        coupon.discount_type = request.POST.get('type')
        coupon.discount_value = request.POST.get('amount')
        coupon.expiration_date = request.POST.get('expiry_date')
        coupon.save()
        return redirect('admin_coupons') 
    return render(request, 'Admin/admin_coupon_edit.html', {'coupon': coupon})

# Admin delete from coupon view
@admin_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    return redirect('admin_coupons')

@login_required
def admin_offers(request):
    offers = Offer.objects.all()  
    return render(request, 'Admin/admin_offers.html', {'offers': offers})

@login_required
def add_offer(request):
    if request.method == 'POST':
        offer_code = request.POST['offer_code']
        offer_type = request.POST['offer_type']
        discount_type = request.POST['discount_type']
        discount_value = request.POST['discount_value']
        starting_date = request.POST['start_date']
        expiration_date = request.POST['end_date']
        is_referral_offer = request.POST.get('is_referral_offer') == 'on'

        try:
            discount_value = Decimal(discount_value)
        except ValueError:
            return render(request, 'Admin/add_offer.html', {'error': 'Invalid discount value'})

        offer = Offer(
            offer_code=offer_code,
            offer_type=offer_type,
            discount_type=discount_type,
            discount_value=discount_value,
            starting_date=starting_date,
            expiration_date=expiration_date,
            is_referral_offer=is_referral_offer
        )
        offer.save()
        return redirect('admin_offers')

    return render(request, 'Admin/add_offer.html')

def edit_offer(request, id):
    offer = get_object_or_404(Offer, id=id) 
    
    if request.method == 'POST': 
        form = OfferForm(request.POST, instance=offer)
        if form.is_valid(): 
            form.save() 
            return redirect('admin_offers') 
    else:
        form = OfferForm(instance=offer)

    return render(request, 'Admin/edit_offers.html', {'form': form})

def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    offer.delete()
    return redirect('admin_offers') 

# Admin settings view
@admin_required
def admin_settings(request):
    return render(request, 'Admin/admin_settings.html')

# Admin logout view
@admin_required
def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('adminn')
