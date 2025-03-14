from razorpay.errors import BadRequestError, ServerError
from PIL import Image
import razorpay
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import simpleSplit
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from django.http import HttpResponse
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import never_cache
from .forms import ProductForm, CategoryForm, CouponForm
from .models import Product, UserProfile, ProductImage, Category, Review, Referral, Coupon, Cart, Address, Order, OrderItem, Wishlist, Payment_model, UserOTP, Offer 
from .models import Wallet
from .models import Profile
from django.core.paginator import Paginator
from django.core.mail import send_mail
from .utils import generate_otp
from django.http import JsonResponse, HttpResponse
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg, Count
from django.utils.timezone import datetime
from django.db import transaction
from urllib.parse import unquote
from . signals import generate_referral_code
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.db.models import DecimalField, F, Sum, Value, IntegerField, Count
from django.db.models import Sum, F, Count, ExpressionWrapper, DecimalField
from django.db.models.functions import Cast, Coalesce
from decimal import Decimal
from django.db import transaction
from django.conf import settings
import json
from io import BytesIO
import os
from .models import Product, Category, OrderItem
from .models import Order, Payment_model, Cart, Address, OrderItem
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Value, DecimalField, IntegerField
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce, Cast
from .models import Order, OrderItem
import datetime
from django.http import HttpResponse
from django.db.models import Sum
from .models import OrderItem
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal
from .models import Cart, Coupon
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as log
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.core.mail import send_mail
from datetime import datetime, timedelta
import re
from .models import Referral, Wallet, UserOTP
import random
import datetime
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.urls import reverse 
from PIL import Image
import razorpay
import openpyxl
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.decorators.cache import never_cache
import datetime 
import re
from .models import Wallet, Referral, Offer, Category, Product
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from .models import Cart, Order, OrderItem, Address, Wallet, Order, OrderItem, Wallet
from datetime import datetime, timedelta
import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from .models import Cart, Offer, Coupon, CouponUsage
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as ReportLabImage
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.core.files.storage import default_storage
import os
from .models import Order, OrderItem



razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

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

def generate_otp():
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def generate_referral_code():
    return ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8)])

def send_otp(email, otp):
    print(f"Attempting to send OTP {otp} to {email}")
    try:
        result = send_mail(
            'Your OTP for Password Reset',
            f'Your OTP is {otp}. Please use it to reset your password.',
            'adarshgs444@gmail.com',
            [email],
            fail_silently=False,
        )
        print(f"OTP {otp} sent to {email}. Result: {result}")
        return True if result == 1 else False
    except Exception as e:
        print(f"Email sending failed for {email}: {str(e)}")
        return False

# Signup View
@never_cache
def signup(request):
    if request.user.is_authenticated:
        return redirect('Home_page')

    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        referral_code = request.POST.get('referral_code', '')
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        allowed_username_regex = r'^[A-Za-z][A-Za-z]{3,}$'
        if not re.match(allowed_username_regex, username):
            messages.error(request, "Username must start with a letter and be at least 4 letters long (letters only).")
            return render(request, 'signup.html', {'username': username, 'email': email})

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' is already taken.")
            return render(request, 'signup.html', {'username': username, 'email': email})
        
        if User.objects.filter(email=email).exists():
            messages.error(request, f"Email '{email}' is already registered.")
            return render(request, 'signup.html', {'username': username, 'email': email})

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'signup.html', {'username': username, 'email': email})

        if not all([username, email, password1, password2]):
            messages.error(request, "All fields are required.")
            return render(request, 'signup.html', {'username': username, 'email': email})

        request.session['username'] = username
        request.session['email'] = email
        request.session['password'] = password1
        request.session['referral_code'] = referral_code

        otp = generate_otp()
        request.session['otp'] = otp
        request.session['otp_creation_time'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

        if send_otp(email, otp):
            messages.success(request, 'OTP sent to your email. Please verify.')
            return redirect('verify_otp')
        else:
            messages.error(request, 'Failed to send OTP. Please check your email address or try again.')
            return render(request, 'signup.html', {'username': username, 'email': email})

    return render(request, 'signup.html')

@never_cache
def verify_otp(request):
    username = request.session.get('username')
    email = request.session.get('email')
    password = request.session.get('password')
    referral_code = request.session.get('referral_code')
    session_otp = request.session.get('otp')
    otp_creation_time_str = request.session.get('otp_creation_time')

    if not all([username, email, password, session_otp, otp_creation_time_str]):
        messages.error(request, "Session expired or missing information. Please sign up again.")
        return redirect('signup')

    naive_otp_creation_time = datetime.datetime.strptime(otp_creation_time_str, '%Y-%m-%d %H:%M:%S')
    otp_creation_time = timezone.make_aware(naive_otp_creation_time, timezone.get_current_timezone())
    expiry_time = otp_creation_time + datetime.timedelta(minutes=1)

    if timezone.now() > expiry_time:
        messages.error(request, "OTP has expired. Please request a new one.")
        return render(request, 'verify_otp.html', {'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S'), 'email': email})

    if request.method == "POST":
        otp = request.POST.get('otp')

        if otp == session_otp:
            user = User.objects.create_user(username=username, email=email, password=password, is_active=True)
            user.save()

            referrer = None
            if referral_code:
                try:
                    referrer = Referral.objects.get(code=referral_code)
                    referrer.referred_users.add(user)
                    referrer.save()

                    referrer_wallet, _ = Wallet.objects.get_or_create(user=referrer.user)
                    referrer_wallet.balance += 100
                    referrer_wallet.save()

                    new_user_wallet = Wallet.objects.create(user=user, balance=50)
                    new_user_wallet.save()
                except Referral.DoesNotExist:
                    pass

            if not referrer:
                Wallet.objects.create(user=user)

            if not Referral.objects.filter(user=user).exists():
                new_referral_code = generate_referral_code()
                Referral.objects.create(user=user, code=new_referral_code)

            for key in ['username', 'email', 'password', 'referral_code', 'otp', 'otp_creation_time']:
                request.session.pop(key, None)

            messages.success(request, 'Account verified successfully. Please log in.')
            return redirect('login_view')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'verify_otp.html', {'expiry_time': expiry_time.strftime('%Y-%m-%d %H:%M:%S'), 'email': email})

# Resend OTP View
@never_cache
def resend_otp(request):
    if request.method == "POST":
        email = request.POST.get('email') or request.session.get('email')
        print(f"Resend OTP requested for email: {email}")
        if not email:
            return JsonResponse({'success': False, 'message': 'Session expired or no email provided. Please sign up again.'})

        new_otp = generate_otp()
        print(f"Generated new OTP: {new_otp}")
        request.session['otp'] = new_otp
        request.session['otp_creation_time'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if send_otp(email, new_otp):
            return JsonResponse({'success': True, 'message': 'A new OTP has been sent to your email. Check your inbox or spam folder.'})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'})

# Login View
@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('Home_page')

    if request.method == "POST":
        email_or_username = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.filter(email=email_or_username).first() or User.objects.filter(username=email_or_username).first()
            if not user:
                messages.error(request, "User not found.")
                return render(request, 'login.html', {'login_input': email_or_username})

            if not user.is_active:
                if UserProfile.objects.filter(user=user, is_active=False).exists():
                    messages.error(request, "The user is blocked.")
                else:
                    messages.error(request, "Please verify your email before logging in.")
                return render(request, 'login.html', {'login_input': email_or_username})

            authenticated_user = authenticate(request, username=user.username, password=password)
            if authenticated_user:
                login(request, authenticated_user)
                messages.success(request, "You have successfully logged in!")
                return redirect('Home_page')
            else:
                messages.error(request, "Incorrect password. Please try again.")
        except Exception as e:
            messages.error(request, str(e))

        return render(request, 'login.html', {'login_input': email_or_username})

    return render(request, 'login.html')

# Password Reset View
@never_cache
def send_reset_otp(request):
    if request.method == 'POST':
        contact = request.POST.get('contact')
        if contact:
            user = User.objects.filter(email=contact).first()
            if user:
                otp = generate_otp()
                print(otp)
                UserOTP.objects.create(user=user, otp=otp)
                if send_otp(contact, otp):
                    return JsonResponse({'success': True, 'message': 'OTP sent to your email. Please verify.'})
                else:
                    return JsonResponse({'success': False, 'message': 'Failed to send OTP. Please try again.'})
            else:
                return JsonResponse({'success': False, 'message': 'No account found with this email.'})
        else:
            return JsonResponse({'success': False, 'message': 'Please enter a valid contact.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})

# Password Reset View
@never_cache
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

    return render(request, 'forget.html')

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
    products = Product.objects.filter(is_deleted=False)
    current_date = timezone.now().date()

    if category_id:
        products = products.filter(category_id=category_id)

    if query:
        products = products.filter(product_name__icontains=query)

    for product in products:
        offer = Offer.objects.filter(
            offer_type='product',
            product=product,
            starting_date__lte=current_date,
            expiration_date__gte=current_date
        ).first() or Offer.objects.filter(
            offer_type='category',
            category=product.category,
            starting_date__lte=current_date,
            expiration_date__gte=current_date
        ).first()

        if offer:
            if offer.discount_type == 'percentage':
                discount = product.sale_price * (offer.discount_value / 100)
                product.sale_price = (product.sale_price - discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                product.offer_message = f"Save {offer.discount_value}%!"
            else:
                product.sale_price = (product.sale_price - offer.discount_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                product.offer_message = f"Save ₹{offer.discount_value}!"
            product.sale_price = max(product.sale_price, Decimal('0'))
        else:
            product.sale_price = product.sale_price
            product.offer_message = None

    if sort_by == 'popularity':
        products = products.annotate(review_count=Count('reviews')).order_by('-review_count')
    elif sort_by == 'average_ratings':
        products = products.annotate(average_rating=Avg('reviews__rating')).order_by('-average_rating') 
    elif sort_by == 'new_arrivals':
        products = products.order_by('-created_at')
    elif sort_by == 'az':
        products = products.order_by('product_name')
    elif sort_by == 'za':
        products = products.order_by('-product_name')

    if filter_by == 'price_low_to_high':
        products = products.order_by('sale_price')
    elif filter_by == 'price_high_to_low':
        products = products.order_by('-sale_price')

    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

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
        'query': query,
        'sort_by': sort_by,
        'filter_by': filter_by,
    })

# Product details view
@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    productss = Product.objects.filter(is_deleted=False)
    related_products = productss.exclude(id=product.id)[:4]
    current_date = timezone.now().date()
    
    offer = Offer.objects.filter(
        offer_type='product',
        product=product,
        starting_date__lte=current_date,
        expiration_date__gte=current_date
    ).first() or Offer.objects.filter(
        offer_type='category',
        category=product.category,
        starting_date__lte=current_date,
        expiration_date__gte=current_date
    ).first()

    offer_message = None
    if offer:
        if offer.discount_type == 'percentage':
            discount = product.sale_price * (offer.discount_value / 100)
            product.sale_price = (product.sale_price - discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            offer_message = f"Save {offer.discount_value}% Now !"
        else:
            product.sale_price = (product.sale_price - offer.discount_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            offer_message = f"Save ₹{offer.discount_value} Now !"
        product.sale_price = max(product.sale_price, Decimal('0'))
    else:
        product.sale_price = product.sale_price

    reviews = product.reviews.all()
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
        related_offer = Offer.objects.filter(
            offer_type='product',
            product=related_product,
            starting_date__lte=current_date,
            expiration_date__gte=current_date
        ).first() or Offer.objects.filter(
            offer_type='category',
            category=related_product.category,
            starting_date__lte=current_date,
            expiration_date__gte=current_date
        ).first()

        if related_offer:
            if related_offer.discount_type == 'percentage':
                discount = related_product.sale_price * (related_offer.discount_value / 100)
                related_product.sale_price = (related_product.sale_price - discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            else:
                related_product.sale_price = (related_product.sale_price - related_offer.discount_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            related_product.sale_price = max(related_product.sale_price, Decimal('0'))
        else:
            related_product.sale_price = related_product.sale_price

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
        'has_purchased': has_purchased,
        'offer_message': offer_message,
    })

@login_required
def buy_now(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    quantity = request.POST.get('quantity', 1)
    selected_color = request.POST.get('selected_color')
    selected_size = request.POST.get('selected_size')

    print(f"Buy Now - POST Data: {request.POST}")
    print(f"Quantity: {quantity}, Color: {selected_color}, Size: {selected_size}")

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
        messages.error(request, f"You can only buy up to {MAX_QTY_PER_PERSON} of {product.product_name}.")
        return redirect('product_detail', product_id=product.id)

    if product.quantity < quantity:
        messages.error(request, f"Only {product.quantity} of {product.product_name} are available.")
        return redirect('product_detail', product_id=product.id)
    Cart.objects.filter(user=request.user).delete()

    cart_item = Cart.objects.create(
        user=request.user,
        product=product,
        quantity=quantity,
        selected_color=selected_color,
        selected_size=selected_size
    )

    messages.success(request, f"{product.product_name} is ready for immediate purchase.")
    return redirect('Checkout')

# Cart view
@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    current_date = timezone.now().date()

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Please add items to proceed.")
        return render(request, 'cart.html', {
            'cart_items': cart_items,
            'total_price': 0,
            'discount': 0,
            'shipping_cost': 0,
            'grand_total': 0,
            'coupon': None,
            'available_coupons': [],
            'coupon_used': False,
        })

    total_price = Decimal('0')
    discount = Decimal(str(request.session.get('discount', 0)))
    coupon = None
    coupon_used = False
    enhanced_cart_items = []
    for item in cart_items:
        offer = Offer.objects.filter(
            offer_type='product',
            product=item.product,
            starting_date__lte=current_date,
            expiration_date__gte=current_date
        ).first() or Offer.objects.filter(
            offer_type='category',
            category=item.product.category,
            starting_date__lte=current_date,
            expiration_date__gte=current_date
        ).first()

        original_price = item.product.sale_price
        if offer:
            if offer.discount_type == 'percentage':
                item_price = (original_price * (1 - offer.discount_value / 100)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                offer_display = f"{offer.discount_value}% Off"
                offer_amount = (original_price - item_price) * item.quantity
            else:
                item_price = (original_price - offer.discount_value).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                offer_display = f"₹{offer.discount_value} Off"
                offer_amount = offer.discount_value * item.quantity
            item_price = max(item_price, Decimal('0'))
        else:
            item_price = original_price
            offer_display = "No Offer"
            offer_amount = Decimal('0')

        item.total_price = (item_price * item.quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_price += item.total_price

        enhanced_cart_items.append({
            'item': item,
            'offer_display': offer_display,
            'offer_amount': offer_amount,
            'original_price': original_price,
            'discounted_price': item_price,
            'total_price': item.total_price
        })

    used_coupon_ids = CouponUsage.objects.filter(user=request.user).values_list('coupon_id', flat=True)
    available_coupons = Coupon.objects.filter(
        is_active=True,
        expiration_date__gte=current_date
    ).exclude(id__in=used_coupon_ids)

    if request.method == "POST":
        if 'coupon_code' in request.POST:
            coupon_code = request.POST.get('coupon_code')
            try:
                coupon = Coupon.objects.get(code=coupon_code, is_active=True)
                if coupon.is_expired():
                    messages.error(request, "The coupon has expired.")
                elif CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
                    messages.error(request, "You have already used this coupon.")
                else:
                    discount = coupon.apply_discount(total_price)
                    messages.success(request, f"Coupon applied! You saved ₹{discount}.")
                    request.session['discount'] = float(discount)
                    request.session['coupon_code'] = coupon.code
                    CouponUsage.objects.create(user=request.user, coupon=coupon)
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")
        
        elif 'remove_coupon' in request.POST:
            discount = Decimal('0')
            messages.success(request, "Coupon removed successfully.")
            request.session.pop('discount', None)
            request.session.pop('coupon_code', None)

    shipping_cost = Decimal('1')
    grand_total = (total_price - discount + shipping_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if grand_total < 0:
        grand_total = Decimal('1')
        messages.warning(request, "Grand total adjusted to minimum due to excessive discount.")

    if 'coupon_code' in request.session:
        try:
            coupon = Coupon.objects.get(code=request.session['coupon_code'])
            coupon_used = CouponUsage.objects.filter(user=request.user, coupon=coupon).exists()
        except Coupon.DoesNotExist:
            coupon = None
            coupon_used = False

    return render(request, 'cart.html', {
        'cart_items': enhanced_cart_items, 
        'total_price': total_price,
        'discount': discount,
        'shipping_cost': shipping_cost,
        'grand_total': grand_total,
        'coupon': coupon,
        'available_coupons': available_coupons,
        'coupon_used': coupon_used,
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
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            message = f"{product.product_name} is already in your wishlist!"
            success = False
        else:
            message = f"{product.product_name} has been added to your wishlist!"
            success = True

        return JsonResponse({'message': message, 'success': success})
    return JsonResponse({'error': 'Invalid request'}, status=400)

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

                if order.status == 'Cancelled':
                    messages.error(request, "Order is already cancelled.")

                elif order.payment_status == 'Confirmed':
                    order.status = 'Cancelled'
                    order.payment_status = 'Cancelled'
                    order.save()

                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    wallet.balance += order.total_price
                    wallet.save()

                    messages.success(request, f'Order cancelled successfully! ₹{order.total_price} has been added to your wallet.')

                elif order.payment_status == 'Pending':  
                    order.status = 'Cancelled'
                    order.payment_status = 'Cancelled'
                    order.save()
                    messages.success(request, "Order cancelled successfully!")

                else:
                    messages.error(request, "Order payment was not confirmed. Refund is not applicable.")

            except Order.DoesNotExist:
                messages.error(request, "Order not found.")


        elif 'return_order' in request.POST:
            order_id = request.POST.get('order_id')
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                
                if order.status == 'Delivered':
                    order.status = 'Returned'
                    order.save()
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    wallet.balance += order.total_price
                    wallet.save()

                    messages.success(request, f'Order returned successfully! ₹{order.total_price} has been added to your wallet.')
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

def generate_razorpay_order_id(grand_total_in_paise):
    print(f"🛠️ Creating Razorpay Order for amount: {grand_total_in_paise} paise")
    data = {
        "amount": grand_total_in_paise,
        "currency": "INR",
        "payment_capture": '1'
    }
    order = client.order.create(data=data)
    print(f"✅ Razorpay Order Created: {order}")
    return order["id"]

# Checkout view
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty. Add items before checking out.")
        return redirect('cart')

    current_date = timezone.now().date()
    total_price = Decimal('0')
    for item in cart_items:
        offer = Offer.objects.filter(
            offer_type='product',
            product=item.product,
            starting_date__lte=current_date,
            expiration_date__gte=current_date
        ).first() or Offer.objects.filter(
            offer_type='category',
            category=item.product.category,
            starting_date__lte=current_date,
            expiration_date__gte=current_date
        ).first()

        if offer:
            if offer.discount_type == 'percentage':
                item_price = item.product.sale_price * (1 - Decimal(offer.discount_value) / 100)
            else:
                item_price = item.product.sale_price - Decimal(offer.discount_value)
            item_price = max(item_price, Decimal('0'))
        else:
            item_price = item.product.sale_price

        total_price += item_price * item.quantity

    total_price = total_price.quantize(Decimal('0.01'))

    discount = Decimal(str(request.session.get('discount', 0))).quantize(Decimal('0.01'))
    shipping_cost = Decimal('1.00')  
    grand_total = (total_price - discount + shipping_cost).quantize(Decimal('0.01'))

    if grand_total <= 0:
        grand_total = Decimal('1.00')
        messages.warning(request, "Grand total adjusted to minimum allowed value due to excessive discount.")

    grand_total_in_paise = int(grand_total * 100)
    existing_addresses = Address.objects.filter(user=request.user)
    razorpay_order_id = generate_razorpay_order_id(grand_total_in_paise)

    print(f"Checkout - Total Price: {total_price}, Discount: {discount}, Shipping: {shipping_cost}, Grand Total: {grand_total}")

    if request.method == "POST":
        payment_method = request.POST.get('payment_method', '').strip()

        if 'delete_address' in request.POST:
            delete_address_id = request.POST.get('delete_address')
            try:
                Address.objects.get(id=delete_address_id, user=request.user).delete()
                messages.success(request, "Address deleted successfully.")
            except Address.DoesNotExist:
                messages.error(request, "Address not found.")
            return redirect('Checkout')

        if 'coupon_code' in request.session:
            try:
                coupon = Coupon.objects.get(code=request.session['coupon_code'], is_active=True)
                if coupon.is_expired():
                    del request.session['discount']
                    del request.session['coupon_code']
                    discount = Decimal('0')
                    grand_total = total_price + shipping_cost
                    grand_total_in_paise = int(grand_total * 100)
                    messages.warning(request, "Coupon expired. Discount removed.")
            except Coupon.DoesNotExist:
                del request.session['discount']
                del request.session['coupon_code']
                discount = Decimal('0')
                grand_total = total_price + shipping_cost
                grand_total_in_paise = int(grand_total * 100)
                messages.warning(request, "Invalid coupon. Discount removed.")

        if payment_method == "cod":
            if grand_total > 1000:
                messages.error(request, "Cash on Delivery is not allowed for orders above Rs 1000.")
                return redirect('Checkout')
            return handle_cod_order(request, cart_items, grand_total, shipping_cost)

        elif payment_method == "razorpay":
            return initiate_razorpay_payment(request, cart_items, grand_total, grand_total_in_paise, shipping_cost, razorpay_order_id)

        elif payment_method == "wallet":
            user_wallet = Wallet.objects.get(user=request.user)
            if user_wallet.balance < grand_total:
                messages.error(request, "Insufficient wallet balance.")
                return redirect('Checkout')
            return handle_wallet_payment(request, cart_items, grand_total, shipping_cost)

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
    print("🚀 initiate_cod_payment called!")
    try:
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_price=grand_total,
                shipping_cost=shipping_cost,
                payment_method="cod",
                payment_status="Pending",
                status="Pending",
            )

            print(f"✅ Order Created: {order.id}")

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_time=item.total_price(),
                    selected_size=item.selected_size,
                    selected_color=item.selected_color,
                    discount=0,
                )
                item.product.quantity -= item.quantity
                item.product.save()

            cart_items.delete()
            request.session.pop('discount', None)
            request.session.pop('coupon_code', None)

        messages.success(request, "Order placed successfully via Cash on Delivery!")
        return redirect('order_complete', order_id=order.id)

    except Exception as e:
        messages.error(request, f"Order failed: {e}")
        return redirect('Checkout')

@csrf_exempt
def initiate_razorpay_payment(request):
    if request.method == "POST":
        print("🚀 initiate_razorpay_payment called!")
        try:
            data = json.loads(request.body)
            print(f"🔍 Received Data: {data}") 
            grand_total = float(data.get("grand_total", 0))
            grand_total_in_paise = int(data.get("grand_total_in_paise", 0))
            print(f"💰 Grand Total: {grand_total} INR, {grand_total_in_paise} paise")

            razorpay_order_id = generate_razorpay_order_id(grand_total_in_paise)

            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_price=grand_total,
                    shipping_cost=1,
                    payment_method="razorpay",
                    payment_status="Confirmed",
                    status="Pending",
                    razorpay_order_id=razorpay_order_id
                )

                print(f"✅ Order Created: {order.id}")

                cart_items = Cart.objects.filter(user=request.user)
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price_at_time=item.total_price(),
                        selected_size=item.selected_size,
                        selected_color=item.selected_color,
                        discount=0,
                    )
                    item.product.quantity -= item.quantity
                    item.product.save()

                cart_items.delete()
                request.session.pop('discount', None)
                request.session.pop('coupon_code', None)

            return JsonResponse({
                "success": True,
                "razorpay_order_id": razorpay_order_id,
                "amount": grand_total_in_paise
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)

def handle_wallet_payment(request, cart_items, grand_total, shipping_cost):
    print("🚀 Wallet Payment Initiated!")
    try:
        with transaction.atomic():
            user_wallet = Wallet.objects.get(user=request.user)
            user_wallet.balance -= grand_total
            user_wallet.save()

            order = Order.objects.create(
                user=request.user,
                total_price=grand_total,
                shipping_cost=shipping_cost,
                payment_method="wallet",
                payment_status="Confirmed",
                status="Pending",
            )

            print(f"✅ Order Created: {order.id}")

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price_at_time=item.total_price(),
                    selected_size=item.selected_size,
                    selected_color=item.selected_color,
                    discount=0,
                )
                item.product.quantity -= item.quantity
                item.product.save()

            cart_items.delete()
            request.session.pop('discount', None)
            request.session.pop('coupon_code', None)

        messages.success(request, "Order placed successfully using Wallet Payment!")
        return redirect('order_complete', order_id=order.id)

    except Exception as e:
        messages.error(request, f"Wallet Payment Failed: {e}")
        return redirect('Checkout')

@csrf_exempt
def order_complete(request, payment_method=None, razorpay_order_id=None, order_id=None):
    order = None
    if payment_method == 'cod' and order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            order.status = 'Completed'
            order.payment_status = 'Success'
            order.save()
            messages.success(request, "Order completed successfully with COD.")
            return render(request, 'order_complete.html', {'message': 'Order completed successfully with COD.'})
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('Checkout')

    elif payment_method == 'wallet' and order_id:
        try:
            order = Order.objects.get(id=order_id, user=request.user)
            if order.payment_status == "Confirmed":
                order.status = 'Completed'
                order.save()
            else:
                messages.error(request, "Payment not confirmed for this order.")
                return redirect('Checkout')
            messages.success(request, "Order completed successfully using Wallet Payment.")
            return render(request, 'order_complete.html', {'message': 'Order completed successfully using Wallet Payment.'})
        except Order.DoesNotExist:
            messages.error(request, "Order not found.")
            return redirect('Checkout')

    elif payment_method == 'razorpay' and razorpay_order_id and order_id:
        if request.method == "POST":
            razorpay_payment_id = request.POST.get("razorpay_payment_id")
            if not razorpay_order_id or not razorpay_payment_id:
                messages.error(request, "Payment processing error: Missing necessary payment details.")
                return redirect('Checkout')
            try:
                order = Order.objects.get(id=order_id, razorpay_order_id=razorpay_order_id, user=request.user)
                if order.payment_status == "Confirmed":
                    with transaction.atomic():
                        order.payment_status = "Confirmed"
                        order.status = "pending"
                        order.save()
                        Payment_model.objects.create(
                            name=order.user.username,
                            amount=str(order.total_price),
                            order_id=razorpay_order_id,
                            razorpay_payment_id=razorpay_payment_id,
                            paid=True
                        )
                    messages.success(request, "Payment successful! Your order is confirmed.")
                    return render(request, 'order_complete.html', {'message': 'Payment successful! Your order is confirmed.'})
                else:
                    messages.error(request, "Payment failed. Please try again.")
            except Order.DoesNotExist:
                messages.error(request, "Order not found.")
                return redirect('Checkout')
            except Exception as e:
                messages.error(request, f"Payment processing error: {e}")
                return redirect('Checkout')
        return render(request, 'order_complete.html', {'message': 'Invalid request method.'})

    return render(request, "order_complete.html", {"status": True})

@login_required
def order_list(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-created_at').prefetch_related("orderitem_set__product")

    if request.method == 'POST':
        if 'cancel_item' in request.POST:
            item_id = request.POST.get('item_id')
            try:
                item = OrderItem.objects.get(id=item_id, order__user=request.user)
                if item.status == 'Cancelled':
                    messages.error(request, f"{item.product.product_name} is already cancelled.")
                elif item.order.payment_status == 'Confirmed':
                    item.status = 'Cancelled'
                    item.save()
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    refund_amount = item.price_at_time
                    wallet.balance += refund_amount
                    wallet.save()
                    messages.success(request, f"{item.product.product_name} cancelled successfully! ₹{refund_amount} added to your wallet.")
                elif item.order.payment_status == 'Pending':
                    item.status = 'Cancelled'
                    item.save()
                    messages.success(request, f"{item.product.product_name} cancelled successfully!")
                else:
                    messages.error(request, "Cannot cancel: Payment not confirmed.")
                order = item.order
                if all(i.status == 'Cancelled' for i in order.orderitem_set.all()):
                    order.payment_status = 'Cancelled'
                    order.save()
            except OrderItem.DoesNotExist:
                messages.error(request, "Order item not found.")

        elif 'return_item' in request.POST:
            item_id = request.POST.get('item_id')
            try:
                item = OrderItem.objects.get(id=item_id, order__user=request.user)
                if item.order.payment_status == 'Confirmed' and item.status == 'Delivered':
                    item.status = 'Returned'
                    item.save()
                    wallet, created = Wallet.objects.get_or_create(user=request.user)
                    refund_amount = item.price_at_time
                    wallet.balance += refund_amount
                    wallet.save()
                    messages.success(request, f"{item.product.product_name} returned successfully! ₹{refund_amount} added to your wallet.")
                else:
                    messages.error(request, f"Cannot return {item.product.product_name}: Not delivered or payment not confirmed.")
            except OrderItem.DoesNotExist:
                messages.error(request, "Order item not found.")

    return render(request, 'orders.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_detail.html', {'order': order})

@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()

    title = Paragraph("<b><font size=18 color='#333'>INVOICE</font></b>", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 16))

    order_details = [
        ["Order ID:", f"{order.id}"],
        ["Date:", f"{order.created_at.strftime('%Y-%m-%d %H:%M')}"],
        ["Total Price:", f"${order.total_price:.2f}"],
        ["Payment Status:", f"{order.payment_status}"],
    ]

    table = Table(order_details, colWidths=[120, 300])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<b><font size=14 color='#444'>Items Purchased:</font></b>", styles["Heading2"]))
    elements.append(Spacer(1, 12))

    data = [["Product", "Qty", "Price", "Image"]]
    
    for item in order.orderitem_set.all():
        product_name = item.product.product_name
        quantity = f"x{item.quantity}"
        price = f"${item.price_at_time:.2f}"

        image_path = None
        if item.product.main_image:
            image_path = default_storage.path(item.product.main_image.name)

        if image_path and os.path.exists(image_path):
            img = ReportLabImage(image_path, width=50, height=50)  
            image_cell = img
        else:
            image_cell = Paragraph("<i>No Image</i>", styles["Italic"])
        data.append([product_name, quantity, price, image_cell])

    items_table = Table(data, colWidths=[220, 60, 80, 100])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))

    footer = Paragraph("<i>Thank you for your purchase!</i>", styles["Italic"])
    elements.append(footer)
    pdf.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{order.id}.pdf"'
    return response

@login_required
def continue_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    return render(request, 'continue_payment.html', {'order': order})

@login_required
def process_payment(request, order_id):
    print(f"process_payment called for order_id: {order_id}")
    order = get_object_or_404(Order, id=order_id, user=request.user)

    total_items_price = OrderItem.objects.filter(
        order=order,
        status__in=['Pending', 'Confirmed', 'Processing', 'Shipped', 'Delivered']
    ).aggregate(total=Sum('price_at_time'))['total'] or Decimal('0')

    shipping_cost = Decimal(str(order.shipping_cost)) if order.shipping_cost else Decimal('0')
    discount = Decimal('0') 
    amount_to_pay = (total_items_price + shipping_cost - discount).quantize(Decimal('0.01'))

    if order.total_price and order.payment_status != "Confirmed":
        amount_to_pay = Decimal(str(order.total_price)).quantize(Decimal('0.01'))

    print(f"Order total_price: {order.total_price}")
    print(f"Total items price (excluding cancelled): {total_items_price}")
    print(f"Shipping cost: {shipping_cost}, Discount: {discount}, Amount to pay: {amount_to_pay}")

    if request.method == "POST":
        payment_method = request.POST.get("payment_method")
        print(f"Payment method selected: {payment_method}")
        if not payment_method:
            return JsonResponse({'success': False, 'error': 'Payment method not provided'}, status=400)

        if payment_method == "wallet":
            user_wallet = Wallet.objects.get(user=request.user)
            if user_wallet.balance < amount_to_pay:
                print(f"Insufficient balance: {user_wallet.balance} < {amount_to_pay}")
                messages.error(request, f"Insufficient wallet balance. Required: ₹{amount_to_pay}, Available: ₹{user_wallet.balance}")
                return redirect('order_list')
            return wallet_payment(request, order, amount_to_pay)

        elif payment_method == "razorpay":
            if amount_to_pay < Decimal('0.50'):
                print("Amount too small")
                return JsonResponse({'success': False, 'error': 'Amount must be at least ₹0.50'}, status=400)
            razorpay_order = razorpay_client.order.create({
                "amount": int(amount_to_pay * 100),
                "currency": "INR",
                "payment_capture": "1"
            })
            request.session['razorpay_order_id'] = razorpay_order['id']
            request.session['order_id'] = order.id
            return JsonResponse({
                'success': True,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': float(amount_to_pay),
                'currency': 'INR',
                'name': request.user.username,
                'email': request.user.email,
            })

    return redirect('order_list')

def wallet_payment(request, order, amount_to_pay):
    try:
        with transaction.atomic():
            user_wallet = Wallet.objects.get(user=request.user)
            print(f"Wallet balance before: {user_wallet.balance}")
            user_wallet.balance -= amount_to_pay
            user_wallet.save()
            print(f"Wallet balance after: {user_wallet.balance}")
            order.payment_status = "Confirmed"
            order.save()
        messages.success(request, f"Payment of ₹{amount_to_pay} completed successfully using Wallet!")
        return redirect('order_complete', payment_method='wallet', order_id=order.id) 
    except Exception as e:
        messages.error(request, f"Wallet payment failed: {e}")
        return redirect('order_list')

@csrf_exempt
def razorpay_payment(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            razorpay_order_id = data.get('razorpay_order_id')
            payment_id = data.get('razorpay_payment_id')
            signature = data.get('razorpay_signature')
            order_id = data.get('order_id') or request.session.get('order_id')

            if not all([razorpay_order_id, payment_id, signature, order_id]):
                return JsonResponse({'success': False, 'error': 'Missing payment details'}, status=400)

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }
            razorpay_client.utility.verify_payment_signature(params_dict)

            order = get_object_or_404(Order, id=order_id, user=request.user)
            order.payment_status = "Confirmed"
            order.save()

            request.session.pop('razorpay_order_id', None)
            request.session.pop('order_id', None)

            messages.success(request, "Payment successful via Razorpay!")
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('order_complete_razorpay_full', args=['razorpay', razorpay_order_id, order.id])
            })
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed.")
            return JsonResponse({'success': False, 'error': 'Signature verification failed'}, status=400)
        except Exception as e:
            print(f"Verification error: {e}")
            messages.error(request, f"Razorpay payment failed: {e}")
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)









from datetime import datetime
import datetime


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
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncMonth, TruncWeek, TruncYear
from .models import OrderItem, Product, Category, Order, User
from datetime import timedelta
from django.utils import timezone

@admin_required
def admin_dashboard(request):
    total_sales = OrderItem.objects.aggregate(
        total_sales=Sum(
            'price_at_time', 
            output_field=DecimalField(max_digits=10, decimal_places=2),
            default=Value(0)
        )
    )['total_sales'] or 0

    top_products = Product.objects.annotate(
        total_sales=Sum('orderitem__quantity')
    ).order_by('-total_sales')[:10]

    top_categories = Category.objects.annotate(
        total_sales=Sum('product__orderitem__quantity')
    ).order_by('-total_sales')[:10]

    recent_sales = Order.objects.order_by('-created_at')[:10]
    total_orders = Order.objects.count()
    total_users = User.objects.count()

    period = request.GET.get('period', 'month')
    time_range = {
        'month': timedelta(days=180), 
        'week': timedelta(days=84), 
        'year': timedelta(days=730), 
    }.get(period, timedelta(days=180))

    start_date = timezone.now() - time_range

    if period == 'month':
        sales_data = OrderItem.objects.filter(
            order__created_at__gte=start_date
        ).annotate(
            period=TruncMonth('order__created_at')
        ).values('period').annotate(
            total=Sum(
                ExpressionWrapper(
                    F('price_at_time') * F('quantity') - F('discount'),
                    output_field=DecimalField()
                )
            )
        ).order_by('period')
        labels = [item['period'].strftime('%b %Y') for item in sales_data]
    elif period == 'week':
        sales_data = OrderItem.objects.filter(
            order__created_at__gte=start_date
        ).annotate(
            period=TruncWeek('order__created_at')
        ).values('period').annotate(
            total=Sum(
                ExpressionWrapper(
                    F('price_at_time') * F('quantity') - F('discount'),
                    output_field=DecimalField()
                )
            )
        ).order_by('period')
        labels = [item['period'].strftime('Week %W, %Y') for item in sales_data]
    elif period == 'year':
        sales_data = OrderItem.objects.filter(
            order__created_at__gte=start_date
        ).annotate(
            period=TruncYear('order__created_at')
        ).values('period').annotate(
            total=Sum(
                ExpressionWrapper(
                    F('price_at_time') * F('quantity') - F('discount'),
                    output_field=DecimalField()
                )
            )
        ).order_by('period')
        labels = [item['period'].strftime('%Y') for item in sales_data]

    sales_values = [float(item['total']) for item in sales_data]

    context = {
        'total_sales': total_sales,
        'top_products': top_products,
        'top_categories': top_categories,
        'recent_sales': recent_sales,
        'total_orders': total_orders,
        'total_users': total_users,
        'sales_labels': labels,
        'sales_data': sales_values,
        'selected_period': period, 
    }

    return render(request, 'Admin/admin_dashboard.html', context)

def generate_ledger(request):
    transactions = OrderItem.objects.all()

    ledger_content = "Date | Invoice No | Customer | Description | Credit (₹) | Balance (₹)\n"
    ledger_content += "-" * 100 + "\n"

    balance = 0
    for transaction in transactions:
        date = transaction.order.created_at.strftime('%Y-%m-%d')
        invoice_no = f"INV-{transaction.order.id:03d}"
        customer = transaction.order.user.username  
        description = f"Purchase of {transaction.product.product_name}"
        
        debit = float(transaction.discount) if transaction.discount else 0.00
        credit = float(transaction.price_at_time) * transaction.quantity
        balance += credit - debit

        ledger_content += f"{date} | {invoice_no} | {customer} | {description} | {credit:.2f} | {balance:.2f}\n"

    response = HttpResponse(ledger_content, content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename="sales_ledger.txt"'
    return response

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
        users = users.order_by('user')
    elif sort_order == 'desc':
        users = users.order_by('-user')

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
            category_name = form.cleaned_data['name']
            if Category.objects.filter(name__iexact=category_name, is_deleted=False).exists():
                messages.error(request, f"A category with the name '{category_name}' already exists (case-insensitive).")
                return render(request, 'Admin/admin_add_category.html', {'form': form})
            else:
                form.save()
                messages.success(request, f"Category '{category_name}' added successfully.")
                return redirect('admin_category')
        else:
            print(form.errors)
            messages.error(request, "Please correct the errors below.")
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
            new_name = form.cleaned_data['name']
            if Category.objects.filter(name__iexact=new_name, is_deleted=False).exclude(id=category_id).exists():
                messages.error(request, f"A category with the name '{new_name}' already exists (case-insensitive).")
                return render(request, 'Admin/admin_edit_category.html', {'form': form})
            else:
                form.save()
                messages.success(request, f"Category updated successfully to '{new_name}'.")
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

            sizes = request.POST.get('sizes')
            if sizes:
                try:
                    sizes_list = [int(size.strip()) for size in sizes.split(',')]
                    product.sizes = json.dumps(sizes_list)
                except ValueError:
                    messages.error(request, "Invalid sizes input. Please enter numbers separated by commas.")
                    return redirect(request.path_info)

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

            product.save()

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

        sizes = request.POST.get('sizes')
        if sizes:
            try:
                sizes_list = [int(size.strip()) for size in sizes.split(',')]
                product.sizes = json.dumps(sizes_list)
            except ValueError:
                messages.error(request, "Invalid sizes input. Please enter numbers separated by commas.")
                return redirect(request.path_info)

        colors = request.POST.get('colors')
        if colors:
            colors_list = [color.strip() for color in colors.split(',')]
            if not all(colors_list):
                messages.error(request, "Invalid colors input. Colors cannot be empty.")
                return redirect(request.path_info)
            product.colors = ','.join(colors_list)
        else:
            product.colors = ""

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
    orders = Order.objects.order_by('-created_at').prefetch_related("orderitem_set__product")

    if request.method == 'POST':
        if 'cancel_item' in request.POST:
            item_id = request.POST.get('item_id')
            try:
                item = OrderItem.objects.get(id=item_id)
                if item.status == 'Cancelled':
                    messages.error(request, f"{item.product.product_name} is already cancelled.")
                elif item.order.payment_status == 'Confirmed':
                    item.status = 'Cancelled'
                    item.save()
                    wallet, created = Wallet.objects.get_or_create(user=item.order.user)
                    refund_amount = item.price_at_time
                    wallet.balance += refund_amount
                    wallet.save()
                    messages.success(request, f"{item.product.product_name} cancelled successfully! ₹{refund_amount} refunded to {item.order.user.username}'s wallet.")
                elif item.order.payment_status == 'Pending':
                    item.status = 'Cancelled'
                    item.save()
                    messages.success(request, f"{item.product.product_name} cancelled successfully!")
                else:
                    messages.error(request, f"Cannot cancel {item.product.product_name}: Payment not confirmed.")

                order = item.order
                if all(i.status == 'Cancelled' for i in order.orderitem_set.all()):
                    order.payment_status = 'Cancelled'
                    order.save()

            except OrderItem.DoesNotExist:
                messages.error(request, "Order item not found.")

    context = {'orders': orders}
    return render(request, 'Admin/admin_orders.html', context)

@admin_required
def update_order_status(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_status = request.POST.get('status')
        
        if not item_id or not new_status:
            messages.error(request, "Missing item ID or status.")
            return redirect('admin_orders') 

        try: 
            item = OrderItem.objects.get(id=item_id)
            item.status = new_status
            item.save()

            order = item.order
            all_delivered = all(i.status == 'Delivered' for i in order.orderitem_set.all())
            all_cancelled = all(i.status == 'Cancelled' for i in order.orderitem_set.all())
            if all_delivered:
                order.payment_status = "Confirmed"
            elif all_cancelled:
                order.payment_status = "Cancelled"
            order.save()

            messages.success(request, f"Item {item.product.product_name} status updated to {new_status}")
        except OrderItem.DoesNotExist:
            messages.error(request, "Order item not found.")
        except Exception as e:
            messages.error(request, f"Error updating status: {str(e)}")

        return redirect('admin_orders')

    messages.error(request, "Invalid request method.")
    return redirect('admin_orders')

# Admin sales
@admin_required
def admin_sales(request):
    orders = get_admin_sales(request)

    total_sales = OrderItem.objects.filter(order__in=orders).aggregate(
        total=Sum(
            'price_at_time', 
            output_field=DecimalField(max_digits=10, decimal_places=2),
            default=Value(0)
        )
    )['total'] or 0

    total_discount = OrderItem.objects.filter(order__in=orders).aggregate(
        total=Coalesce(
            Sum('discount', output_field=DecimalField(max_digits=10, decimal_places=2)),
            Value(0, output_field=DecimalField(max_digits=10, decimal_places=2))
        )
    )['total']

    total_orders = orders.count()

    print(f"Total Sales: {total_sales}, Total Discount: {total_discount}, Total Orders: {total_orders}")
    print("Discount values:", [item.discount for item in OrderItem.objects.filter(order__in=orders)])

    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_orders = paginator.get_page(page_number)

    context = {
        'total_sales': total_sales,
        'total_discount': total_discount,
        'total_orders': total_orders,
        'orders': page_orders,
    }
    return render(request, 'Admin/admin_sales_report.html', context)

def get_admin_sales(request):
    period = request.GET.get('period')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    today = timezone.now().date()
    orders = Order.objects.all()

    if period == 'daily':
        orders = orders.filter(created_at__date=today)
    elif period == 'weekly':
        week_ago = today - datetime.timedelta(days=7)
        orders = orders.filter(created_at__gte=week_ago)
    elif period == 'monthly':
        month_start = today.replace(day=1)
        orders = orders.filter(created_at__gte=month_start)
    elif start_date and end_date:
        try:
            start = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.datetime.strptime(end_date, '%Y-%m-%d') + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)
            if settings.USE_TZ:
                start = timezone.make_aware(start, timezone.get_current_timezone())
                end = timezone.make_aware(end, timezone.get_current_timezone())
            orders = orders.filter(created_at__range=[start, end])
        except ValueError:
            orders = Order.objects.none()
    else:
        orders = orders.all()

    return orders

def download_report(request, file_type):
    orders = get_admin_sales(request)
    if file_type == 'pdf':
        response = generate_pdf_report(orders)
    elif file_type == 'excel':
        response = generate_excel_report(orders)
    return response

def generate_pdf_report(orders):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    p.setFont("Helvetica-Bold", 16)
    p.drawString(250, height - 50, "Sales Report")
    p.setFont("Helvetica-Bold", 12)
    col_positions = [30, 100, 170, 310, 340, 440, 520]

    headers = ["Order ID", "Customer", "Product Name", "Qty", "Category", "Amount", "Date"]
    for i, header in enumerate(headers):
        p.drawString(col_positions[i], height - 100, header)

    y_position = height - 120
    p.setFont("Helvetica", 10)

    for order in orders:
        for order_item in order.orderitem_set.all():
            row_data = [
                str(order.id),
                order.user.username if order.user else "N/A",
                order_item.product.product_name if order_item.product else "N/A",
                str(order_item.quantity),
                order_item.product.category.name if order_item.product.category else "N/A",
                f"{order.total_price}",
                order.created_at.strftime("%Y-%m-%d"),
            ]

            for i, data in enumerate(row_data):
                if i + 1 < len(col_positions):
                    column_width = col_positions[i + 1] - col_positions[i] - 5
                else:
                    column_width = 50 

                wrapped_text = simpleSplit(data, "Helvetica", 10, column_width)
                p.drawString(col_positions[i], y_position, wrapped_text[0] if wrapped_text else "")

            y_position -= 20

            if y_position < 50:
                p.showPage()
                y_position = height - 100

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

        if Coupon.objects.filter(code__iexact=code).exists():
            messages.error(request, f"A coupon with the code '{code}' already exists. Please use a different code.")
            return redirect('admin_add_coupon')

        try:
            Coupon.objects.create(
                code=code,
                discount_type=discount_type,
                discount_value=discount_value,
                expiration_date = datetime.datetime.strptime(expiration_date, '%Y-%m-%d'),
                is_active=True
            )
            messages.success(request, f"Coupon '{code}' added successfully!")
            return redirect('admin_coupons')

        except ValueError as e:
            messages.error(request, f"Invalid input: {e}")
            return redirect('admin_add_coupon')

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
        messages.success(request, f"Coupon updated successfully!")
        return redirect('admin_coupons') 
    return render(request, 'Admin/admin_coupon_edit.html', {'coupon': coupon})

# Admin delete from coupon view
@admin_required
def delete_coupon(request, coupon_id):
    coupon = get_object_or_404(Coupon, id=coupon_id)
    coupon.delete()
    messages.success(request, f"Coupon deleted successfully!")
    return redirect('admin_coupons')

@admin_required
def admin_offers(request):
    offers = Offer.objects.all()  
    return render(request, 'Admin/admin_offers.html', {'offers': offers})

@admin_required
def add_offer(request):
    categories = Category.objects.filter(is_deleted=False)
    products = Product.objects.filter(is_deleted=False)
    error = None

    if request.method == 'POST':
        offer_type = request.POST.get('offer_type')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        starting_date = request.POST.get('start_date')
        expiration_date = request.POST.get('end_date')
        product_id = request.POST.get('product')
        category_id = request.POST.get('category')

        if not all([offer_type, discount_type, discount_value, starting_date, expiration_date]):
            error = "All fields are required."
        else:
            try:
                discount_value = Decimal(discount_value)
                if discount_value <= 0:
                    error = "Discount value must be positive."
                    raise ValueError("Invalid discount value")

                start = timezone.datetime.strptime(starting_date, '%Y-%m-%d').date()
                end = timezone.datetime.strptime(expiration_date, '%Y-%m-%d').date()
                if start > end:
                    error = "Start date must be before end date."
                    raise ValueError("Invalid date range")
                if end < timezone.now().date():
                    error = "Expiration date must be in the future."
                    raise ValueError("Expired offer")

                offer = Offer(
                    offer_type=offer_type,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    starting_date=starting_date,
                    expiration_date=expiration_date,
                    is_referral_offer=False 
                )
                if offer_type == 'product' and product_id:
                    offer.product_id = int(product_id)
                elif offer_type == 'category' and category_id:
                    offer.category_id = int(category_id)
                elif offer_type not in ['product', 'category']:
                    error = "Invalid offer type."
                    raise ValueError("Invalid offer type")

                offer.save()
                messages.success(request, "Offer added successfully!")
                return redirect('admin_offers')
            except ValueError as ve:
                if not error: 
                    error = str(ve)
            except Exception as e:
                print(f"Error adding offer: {e}")
                error = f"Failed to add offer: {str(e)}"

        if error:
            messages.error(request, error)

    return render(request, 'Admin/add_offer.html', {
        'categories': categories,
        'products': products,
        'error': error,
        'form_data': request.POST if request.method == 'POST' else None
    })

@admin_required
def edit_offer(request, id):
    offer = get_object_or_404(Offer, id=id)
    categories = Category.objects.filter(is_deleted=False)
    products = Product.objects.filter(is_deleted=False)
    error = None

    if request.method == 'POST':
        offer_type = request.POST.get('offer_type')
        discount_type = request.POST.get('discount_type')
        discount_value = request.POST.get('discount_value')
        starting_date = request.POST.get('start_date')
        expiration_date = request.POST.get('end_date')
        product_id = request.POST.get('product')
        category_id = request.POST.get('category')

        if not all([offer_type, discount_type, discount_value, starting_date, expiration_date]):
            error = "All fields are required."
        else:
            try:
                discount_value = Decimal(discount_value)
                if discount_value <= 0:
                    error = "Discount value must be positive."
                    raise ValueError("Invalid discount value")

                start = timezone.datetime.strptime(starting_date, '%Y-%m-%d').date()
                end = timezone.datetime.strptime(expiration_date, '%Y-%m-%d').date()
                if start > end:
                    error = "Start date must be before end date."
                    raise ValueError("Invalid date range")
                if end < timezone.now().date():
                    error = "Expiration date must be in the future."
                    raise ValueError("Expired offer")

                offer.offer_type = offer_type
                offer.discount_type = discount_type
                offer.discount_value = discount_value
                offer.starting_date = starting_date
                offer.expiration_date = expiration_date
                offer.is_referral_offer = False

                if offer_type == 'product' and product_id:
                    offer.product_id = int(product_id)
                    offer.category_id = None
                elif offer_type == 'category' and category_id:
                    offer.category_id = int(category_id)
                    offer.product_id = None
                elif offer_type not in ['product', 'category']:
                    error = "Invalid offer type."
                    raise ValueError("Invalid offer type")
                else:
                    offer.product_id = None
                    offer.category_id = None

                offer.save()
                messages.success(request, "Offer updated successfully!")
                return redirect('admin_offers')
            except ValueError as ve:
                if not error:
                    error = str(ve)
            except Exception as e:
                print(f"Error updating offer: {e}")
                error = f"Failed to update offer: {str(e)}"

        if error:
            messages.error(request, error)

    return render(request, 'Admin/edit_offers.html', {
        'offer': offer,
        'categories': categories,
        'products': products,
        'error': error,
        'form_data': request.POST if request.method == 'POST' else None
    })

@admin_required
def delete_offer(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    offer.delete()
    return redirect('admin_offers') 

# Admin settings view
@admin_required
def admin_settings(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        profile.mobile = request.POST.get('mobile', profile.mobile)
        profile.dob = request.POST.get('dob', profile.dob) or None
        password = request.POST.get('password', '')

        if password:
            user.set_password(password)

        if 'profile_pic' in request.FILES:
            profile.profile_pic = request.FILES['profile_pic']

        try:
            user.save()
            profile.save()
            messages.success(request, 'Your information has been updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating information: {str(e)}')

        return redirect('admin_settings')

    context = {
        'user': user,
        'profile': profile,
    }
    return render(request, 'Admin/admin_settings.html', context)

# Admin logout view
@admin_required
def admin_logout(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('adminn')
